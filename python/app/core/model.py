"""
Base ActiveRecord Model implementation for CropSense AI ORM.
Supports fluent query builder (.where, .and_where, .or_where, .order_by, .limit, .offset, .paginate),
CRUD operations (.get, .first, .find, .create, .update, .save, .delete, .upsert),
fillable column protection, relationship resolution, and FastAPI serialization.
"""
from __future__ import annotations

import datetime
from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, TypeVar, Union

from app.core.db import DB

T = TypeVar("T", bound="Model")


class Model:
    """ActiveRecord Base Model."""

    table: str = ""
    primary_key: str = "id"
    fillable: List[str] = []
    relations: Dict[str, Dict[str, Any]] = {}

    def __init__(self, **attributes: Any) -> None:
        # Internal query builder state
        self._where_clauses: List[Tuple[str, str, Any, str]] = []  # (field, op, value, logic)
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._eager_relations: List[str] = []

        # Model instance attributes
        self._attributes: Dict[str, Any] = {}
        self._loaded_relations: Dict[str, Any] = {}

        if attributes:
            self._fill_attributes(attributes)

    # ------------------------------------------------------------------
    # Attribute Access & Serialization
    # ------------------------------------------------------------------
    def _fill_attributes(self, data: Dict[str, Any]) -> None:
        """Populate instance attributes."""
        for key, value in data.items():
            self._attributes[key] = value

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or "_attributes" not in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        if name in self._attributes:
            return self._attributes[name]

        # Lazy resolve relation if defined
        if name in self.relations:
            if name not in self._loaded_relations:
                self._load_relation(name)
            return self._loaded_relations.get(name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in (
            "table",
            "primary_key",
            "fillable",
            "relations",
        ):
            super().__setattr__(name, value)
        else:
            if hasattr(self, "_attributes"):
                self._attributes[name] = value
            else:
                super().__setattr__(name, value)

    def __getitem__(self, item: str) -> Any:
        return self._attributes[item]

    def __setitem__(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def __contains__(self, item: str) -> bool:
        return item in self._attributes

    def __iter__(self) -> Iterator[str]:
        return iter(self._attributes)

    def get(self, key: str, default: Any = None) -> Any:
        return self._attributes.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model instance to dictionary."""
        out = deepcopy(self._attributes)
        for rel_name, rel_val in self._loaded_relations.items():
            if isinstance(rel_val, Model):
                out[rel_name] = rel_val.to_dict()
            elif isinstance(rel_val, list):
                out[rel_name] = [item.to_dict() if isinstance(item, Model) else item for item in rel_val]
            else:
                out[rel_name] = rel_val
        return out

    def dict(self) -> Dict[str, Any]:
        """Pydantic compatibility method."""
        return self.to_dict()

    def model_dump(self) -> Dict[str, Any]:
        """Pydantic v2 compatibility method."""
        return self.to_dict()

    # ------------------------------------------------------------------
    # Query Builder Methods
    # ------------------------------------------------------------------
    def where(self: T, field: str, value_or_op: Any, value: Any = None) -> T:
        """Add WHERE condition."""
        clone = deepcopy(self)
        if value is None:
            operator = "="
            val = value_or_op
        else:
            operator = value_or_op
            val = value
        clone._where_clauses.append((field, operator, val, "AND"))
        return clone

    def and_where(self: T, field: str, value_or_op: Any, value: Any = None) -> T:
        """Chain additional AND WHERE condition."""
        return self.where(field, value_or_op, value)

    def or_where(self: T, field: str, value_or_op: Any, value: Any = None) -> T:
        """Chain OR WHERE condition."""
        clone = deepcopy(self)
        if value is None:
            operator = "="
            val = value_or_op
        else:
            operator = value_or_op
            val = value
        clone._where_clauses.append((field, operator, val, "OR"))
        return clone

    def order_by(self: T, column: str, direction: str = "ASC") -> T:
        """Order by column."""
        clone = deepcopy(self)
        clone._order_by.append(f"{column} {direction.upper()}")
        return clone

    def limit(self: T, count: int) -> T:
        """Set query limit."""
        clone = deepcopy(self)
        clone._limit = count
        return clone

    def offset(self: T, count: int) -> T:
        """Set query offset."""
        clone = deepcopy(self)
        clone._offset = count
        return clone

    def paginate(self: T, limit: int = 20, offset: int = 0) -> List[T]:
        """Paginate results."""
        return self.limit(limit).offset(offset).get()

    def with_rel(self: T, *relation_names: str) -> T:
        """Specify relationships to eager-load."""
        clone = deepcopy(self)
        clone._eager_relations.extend(relation_names)
        return clone

    # ------------------------------------------------------------------
    # SQL Execution & Compilation
    # ------------------------------------------------------------------
    def _build_select_sql(self) -> Tuple[str, Dict[str, Any]]:
        """Construct SELECT statement from clauses."""
        sql = f"SELECT * FROM {self.table}"
        params: Dict[str, Any] = {}

        if self._where_clauses:
            parts = []
            for i, (field, op, val, logic) in enumerate(self._where_clauses):
                param_name = f"p_{field}_{i}"
                prefix = "" if i == 0 else f" {logic} "
                if op.upper() in ("IN", "NOT IN") and isinstance(val, (list, tuple)):
                    in_placeholders = []
                    for j, item in enumerate(val):
                        item_param = f"{param_name}_{j}"
                        in_placeholders.append(f"%({item_param})s")
                        params[item_param] = item
                    parts.append(f"{prefix}{field} {op} ({', '.join(in_placeholders)})")
                elif op.upper() in ("IS NULL", "IS NOT NULL"):
                    parts.append(f"{prefix}{field} {op}")
                else:
                    parts.append(f"{prefix}{field} {op} %({param_name})s")
                    params[param_name] = val
            sql += " WHERE " + "".join(parts)

        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
        else:
            sql += f" ORDER BY {self.primary_key} DESC"

        if self._limit is not None:
            sql += f" LIMIT {int(self._limit)}"
        if self._offset is not None:
            sql += f" OFFSET {int(self._offset)}"

        return sql, params

    def get(self: T) -> List[T]:
        """Execute SELECT query and return list of model instances."""
        sql, params = self._build_select_sql()
        raw_rows = DB.raw(sql, params).exe().rows
        instances: List[T] = []
        for row in raw_rows:
            inst = self.__class__(**row)
            if self._eager_relations:
                for rel in self._eager_relations:
                    inst._load_relation(rel)
            instances.append(inst)
        return instances

    def first(self: T) -> Optional[T]:
        """Return the first record matching the query, or None."""
        results = self.limit(1).get()
        return results[0] if results else None

    @classmethod
    def find(cls: Type[T], item_id: Any) -> Optional[T]:
        """Find a single record by primary key."""
        return cls().where(cls.primary_key, item_id).first()

    # ------------------------------------------------------------------
    # Persistence & Mutations
    # ------------------------------------------------------------------
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out fields that are not in the fillable list."""
        if not self.fillable:
            return data
        allowed = set(self.fillable) | {self.primary_key, "id", "created_at", "updated_at"}
        return {k: v for k, v in data.items() if k in allowed}

    @classmethod
    def create(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a new record in the database."""
        instance = cls()
        clean = instance._sanitize_data(data)

        # Automatically manage timestamps
        now = datetime.datetime.now(datetime.timezone.utc)
        if "created_at" in instance.fillable or "created_at" not in clean:
            clean.setdefault("created_at", now)
        if "updated_at" in instance.fillable or "updated_at" not in clean:
            clean.setdefault("updated_at", now)
        if "enable" not in clean:
            clean["enable"] = 1

        cols = [k for k in clean.keys() if k != cls.primary_key]
        placeholders = [f"%({col})s" for col in cols]

        sql = f"INSERT INTO {cls.table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING *"
        params = {col: clean[col] for col in cols}

        res = DB.raw(sql, params).exe()
        row = res.first()
        if not row:
            # Fallback if SQLite last_id returned without RETURNING clause
            created_id = res.last_id or 1
            clean[cls.primary_key] = created_id
            row = clean

        return cls(**row)

    def save(self) -> "Model":
        """Persist current instance changes to database."""
        now = datetime.datetime.now(datetime.timezone.utc)
        pk_val = self._attributes.get(self.primary_key)

        if pk_val is not None:
            # Update
            self._attributes["updated_at"] = now
            cols = [
                k
                for k in self._attributes.keys()
                if k != self.primary_key and (not self.fillable or k in self.fillable or k == "updated_at")
            ]
            set_clauses = [f"{col} = %({col})s" for col in cols]
            sql = f"UPDATE {self.table} SET {', '.join(set_clauses)} WHERE {self.primary_key} = %(pk)s RETURNING *"
            params = {col: self._attributes[col] for col in cols}
            params["pk"] = pk_val
            res = DB.raw(sql, params).exe().first()
            if res:
                self._fill_attributes(res)
            return self
        else:
            # Insert
            created = self.create(self._attributes)
            self._fill_attributes(created.to_dict())
            return self

    def update(self, data: Optional[Dict[str, Any]] = None) -> "Model":
        """Update instance attributes and save."""
        if data:
            clean = self._sanitize_data(data)
            for k, v in clean.items():
                self._attributes[k] = v
        return self.save()

    def delete(self) -> bool:
        """Delete instance record from database."""
        pk_val = self._attributes.get(self.primary_key)
        if pk_val is None:
            return False
        sql = f"DELETE FROM {self.table} WHERE {self.primary_key} = %(pk)s"
        DB.raw(sql, {"pk": pk_val}).exe()
        return True

    @classmethod
    def upsert(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create or update based on primary key existence."""
        pk = data.get(cls.primary_key)
        if pk:
            existing = cls.find(pk)
            if existing:
                existing.update(data)
                return existing
        return cls.create(data)

    # ------------------------------------------------------------------
    # Relationship Loader
    # ------------------------------------------------------------------
    def _load_relation(self, relation_name: str) -> None:
        """Resolve defined relationship dynamically."""
        rel_spec = self.relations.get(relation_name)
        if not rel_spec:
            return

        try:
            rel_model_cls = rel_spec["callback"]()
            local_key = rel_spec["name"]
            foreign_key = rel_spec["key"]
            local_val = self._attributes.get(local_key)

            if local_val is None:
                self._loaded_relations[relation_name] = None
                return

            # Check if one-to-one or one-to-many
            target_instance = rel_model_cls().where(foreign_key, local_val).first()
            self._loaded_relations[relation_name] = target_instance
        except Exception:
            self._loaded_relations[relation_name] = None
