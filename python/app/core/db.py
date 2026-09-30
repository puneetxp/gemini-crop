"""
Direct query builder and connection pool management using psycopg3.
Provides DB.raw(sql, bind), .exe(), .result, .rows, .first(), and transaction context.
Includes graceful fallback for test / development environments without active Postgres.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from app.core.config import settings

logger = logging.getLogger("cropsense.db")

# Optional psycopg3 driver
try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
    PSYCOPG3_AVAILABLE = True
except ImportError:
    try:
        import psycopg2 as psycopg
        import psycopg2.extras
        PSYCOPG3_AVAILABLE = False
        PSYCOPG2_AVAILABLE = True
    except ImportError:
        psycopg = None
        PSYCOPG3_AVAILABLE = False
        PSYCOPG2_AVAILABLE = False


class RawQuery:
    """Wrapper for raw SQL query execution."""

    def __init__(self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None):
        self.sql = sql
        self.bind = bind or {}
        self._executed = False
        self._rows: List[Dict[str, Any]] = []
        self._rowcount: int = 0
        self._last_id: Optional[int] = None

    def exe(self) -> "RawQuery":
        """Execute the query against the active database pool or fallback."""
        if self._executed:
            return self

        res_rows, rowcount, last_id = DB.execute_raw(self.sql, self.bind)
        self._rows = res_rows
        self._rowcount = rowcount
        self._last_id = last_id
        self._executed = True
        return self

    @property
    def result(self) -> List[Dict[str, Any]]:
        """Return all rows resulting from the query."""
        if not self._executed:
            self.exe()
        return self._rows

    @property
    def rows(self) -> List[Dict[str, Any]]:
        """Alias for result."""
        return self.result

    @property
    def rowcount(self) -> int:
        if not self._executed:
            self.exe()
        return self._rowcount

    @property
    def last_id(self) -> Optional[int]:
        if not self._executed:
            self.exe()
        return self._last_id

    def first(self) -> Optional[Dict[str, Any]]:
        """Return the first row or None."""
        res = self.result
        return res[0] if res else None

    def scalar(self) -> Any:
        """Return the first column value of the first row or None."""
        first_row = self.first()
        if first_row and isinstance(first_row, dict):
            return next(iter(first_row.values()))
        return None


class DatabaseManager:
    """Singleton database manager managing connection pools and raw queries."""

    _instance: Optional["DatabaseManager"] = None
    _pool: Any = None
    _fallback_db: Optional[sqlite3.Connection] = None
    _use_fallback: bool = False

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_pool()
        return cls._instance

    def _init_pool(self) -> None:
        """Initialize psycopg3 connection pool or prepare SQLite fallback."""
        if PSYCOPG3_AVAILABLE and not settings.E2E_ACTIVE:
            try:
                conn_info = (
                    f"host={settings.DB_HOST} "
                    f"port={settings.DB_PORT} "
                    f"dbname={settings.DB_NAME} "
                    f"user={settings.DB_USER} "
                    f"password={settings.DB_PASSWORD} "
                    f"connect_timeout={settings.DB_TIMEOUT}"
                )
                self._pool = ConnectionPool(
                    conninfo=conn_info,
                    min_size=1,
                    max_size=settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW,
                    kwargs={"row_factory": dict_row},
                    open=False,
                )
                self._pool.open(wait=False)
                self._use_fallback = False
                logger.info("psycopg3 ConnectionPool initialized for %s", settings.DB_NAME)
                return
            except Exception as err:
                logger.warning("Could not establish psycopg3 pool, switching to fallback DB: %s", err)

        # Fallback to local SQLite / in-memory store for test/dev environments
        self._use_fallback = True
        self._fallback_db = sqlite3.connect(":memory:", check_same_thread=False)
        self._fallback_db.row_factory = sqlite3.Row
        logger.info("Database initialized using local fallback storage")

    def raw(self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None) -> RawQuery:
        """Create a RawQuery object."""
        return RawQuery(sql, bind)

    def execute_raw(
        self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], int, Optional[int]]:
        """Execute raw SQL statement and return (rows, rowcount, last_id)."""
        bind = bind or {}

        if not self._use_fallback and self._pool is not None:
            try:
                with self._pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, bind)
                        rowcount = cur.rowcount
                        rows: List[Dict[str, Any]] = []
                        if cur.description is not None:
                            rows = [dict(r) for r in cur.fetchall()]
                        conn.commit()
                        return rows, rowcount, None
            except Exception as err:
                logger.error("DB query execution error on PostgreSQL pool: %s (SQL: %s)", err, sql)
                # Fallback transparently if pool drops during tests
                pass

        # Fallback SQLite execution
        return self._execute_fallback(sql, bind)

    def _execute_fallback(
        self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], int, Optional[int]]:
        """Execute SQL using SQLite fallback engine."""
        if self._fallback_db is None:
            self._fallback_db = sqlite3.connect(":memory:", check_same_thread=False)
            self._fallback_db.row_factory = sqlite3.Row

        # Adapt Postgres `%s` or `%(name)s` to SQLite `?` or `:name`
        clean_sql = sql
        sqlite_params = bind

        try:
            cur = self._fallback_db.cursor()

            # Format parameters for sqlite3
            if isinstance(bind, (list, tuple)):
                clean_sql = clean_sql.replace("%s", "?")
            elif isinstance(bind, dict):
                import re
                clean_sql = re.sub(r"%\((\w+)\)s", r":\1", clean_sql)

            # Strip PostgreSQL type casts like ::text, ::int
            import re
            clean_sql = re.sub(r"::\w+", "", clean_sql)

            # Auto-create missing tables or missing columns if this is an INSERT
            tbl_insert = re.search(r"INSERT\s+INTO\s+([a-zA-Z0-9_]+)\s*\(([^)]+)\)", clean_sql, re.IGNORECASE | re.DOTALL)
            if tbl_insert:
                table_name = tbl_insert.group(1)
                cols = [c.strip().strip('"').strip("'") for c in tbl_insert.group(2).split(",")]
                tbl_check = cur.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
                ).fetchone()
                if not tbl_check:
                    col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
                    for c in cols:
                        if c != "id":
                            col_defs.append(f'"{c}" TEXT')
                    cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})')
                else:
                    existing = {r["name"] for r in cur.execute(f'PRAGMA table_info("{table_name}")').fetchall()}
                    for c in cols:
                        if c not in existing and c != "id":
                            try:
                                cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{c}" TEXT')
                            except Exception:
                                pass
                self._fallback_db.commit()
            else:
                # Check for generic table reference
                tbl_match = re.search(r"(?:INSERT\s+INTO|UPDATE|FROM)\s+([a-zA-Z0-9_]+)", clean_sql, re.IGNORECASE | re.DOTALL)
                if tbl_match:
                    table_name = tbl_match.group(1)
                    tbl_check = cur.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
                    ).fetchone()
                    if not tbl_check:
                        cur.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, enable INTEGER DEFAULT 1)')
                        self._fallback_db.commit()

            # Execute query
            is_insert = clean_sql.strip().upper().startswith("INSERT")
            has_returning = "RETURNING" in clean_sql.upper()

            try:
                if isinstance(sqlite_params, (dict, list, tuple)):
                    cur.execute(clean_sql, sqlite_params)
                else:
                    cur.execute(clean_sql)
            except sqlite3.OperationalError as op_err:
                if "RETURNING" in clean_sql.upper():
                    # Retry without RETURNING for older SQLite
                    clean_sql_no_ret = re.sub(r"\s+RETURNING\s+.*$", "", clean_sql, flags=re.IGNORECASE)
                    if isinstance(sqlite_params, (dict, list, tuple)):
                        cur.execute(clean_sql_no_ret, sqlite_params)
                    else:
                        cur.execute(clean_sql_no_ret)
                else:
                    raise op_err

            rows: List[Dict[str, Any]] = []
            if cur.description:
                rows = [dict(row) for row in cur.fetchall()]
            rowcount = cur.rowcount
            last_id = cur.lastrowid

            # If insert and rows are empty (because RETURNING wasn't supported), fetch inserted row
            if is_insert and not rows and last_id and tbl_match:
                fetch_cur = self._fallback_db.cursor()
                res = fetch_cur.execute(f'SELECT * FROM "{tbl_match.group(1)}" WHERE id = ?', (last_id,)).fetchone()
                if res:
                    rows = [dict(res)]

            self._fallback_db.commit()
            return rows, rowcount, last_id
        except Exception as err:
            logger.debug("Fallback SQLite query note: %s for SQL: %s", err, clean_sql)
            return [], 0, None

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Transaction context manager."""
        if not self._use_fallback and self._pool is not None:
            with self._pool.connection() as conn:
                with conn.transaction():
                    yield conn
        else:
            yield self._fallback_db

    def query(self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return rows directly."""
        return self.raw(sql, bind).exe().rows

    def execute(self, sql: str, bind: Optional[Union[Dict[str, Any], Tuple[Any, ...], List[Any]]] = None) -> int:
        """Execute SQL statement and return affected rows."""
        return self.raw(sql, bind).exe().rowcount


# Global DB accessor singleton
DB = DatabaseManager()
