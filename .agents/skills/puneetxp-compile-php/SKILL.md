---
name: the-framework
description: >
  Design, build, extend, and debug applications using the "the" framework family by
  puneetxp: the schema-first generator (puneetxp/compile-php + setup.php), the PHP runtime
  (puneetxp/the / the_lib), the Deno runtime (@puneetxp/the / the_deno), the Python/FastAPI
  output, and the Angular (the-angular), SolidJS (the-solid-router), and Vue frontends. Use this skill when working in
  repositories prefixed with `the_`, `the-`, or `the`, or in apps built on them (e.g. the_billing / INTAX).
  Trigger on mentions of: 'the framework', 'the_lib', 'compile-php', 'setup.php', 'autosetup.php',
  'TPHP', 'puneetxp/the', 'the_deno', '@puneetxp/the', 'the-angular', 'the-solid-router',
  `database/Model/*.json`, `config.json` "back-end"/"front-end", or role namespaces isuper/islogin/ipublic.
---

# The Framework ("the")

A schema-first framework family created by Puneet Sharma (`puneetxp`). You describe each table **once** in JSON (`database/Model/*.json`). The generator `puneetxp/compile-php` then writes the SQL DDL, a role-guarded REST backend (Python FastAPI, Deno, PHP, .NET, Go, or Java Spring), and typed frontend code (SolidJS, Angular, or Vue). The generated code runs on small per-language runtimes that share the same concepts: a `Model` ORM with eager relations, a router with `islogin`/`roles`/`guard`, and a CRUD shorthand.

---

## 0. Repository Map (under `/Users/waseemakram/Downloads/puneetxp/` & `vendor/puneetxp`)

| Repo / Folder | Role | Package / Status |
|---|---|---|
| `compile-php` | **The generator**, plus the HTML→PHP view compiler | Composer `puneetxp/compile-php` (PSR-4: `Puneetxp\CompilePhp\`). Active. |
| `the_lib` | PHP runtime (`The\` namespace) | Composer `puneetxp/the` (tag 0.1.304, PHP ≥ 8.2). Active. |
| `the_deno` | Deno runtime | JSR `@puneetxp/the` 0.1.16 (HEAD). Apps may still pin deno.land/x `the@0.0.2`. |
| `the_template_php` | Starter template (`composer create-project`) | Composer `puneetxp/the_template_php`. |
| `the-angular` | Angular UI library | npm `the-angular` 0.0.13, Angular 21. Active. |
| `the-angular-material` | Angular 16 predecessor | Legacy. |
| `the_web_component` | Vanilla custom elements (`<editable-list>`, `<wysiwyg-bs>`) | Prototype. |
| `the_dotnet` / `the_dotnet_api` | .NET 10 runtime port and sample API | Supported via `dotnetset.php`. |
| `the_go` | Go/Gin helper skeletons | Supported via `golangset.php`. |
| `the_spring` | Java Spring Boot helper skeletons | Supported via `javaspringset.php`. |
| `the_billing` | INTAX GST billing app (Deno + SolidJS + MySQL) | The reference Deno app at `/Users/waseemakram/Documents/the_billing`. |
| `intaxing23` | intaxing.in production app (PHP + Angular + MySQL) | The reference PHP app. |
| `apac-genaiacademy-c2` | Rural farming platform (Python/FastAPI + SolidJS + PostgreSQL), at `/Users/waseemakram/Documents/apac-genaiacademy-c2` | The gold-standard Python/FastAPI reference app, and source of `python/app/core`. |
| `the_doc` | Hugo/Doks documentation site | `content/en/docs/**` |

---

## 1. Generator Workflow & CLI

1. **Declare schema in `database/Model/<name>.json`**. **Never hand-edit generated SQL or models.**
2. Run `php setup.php` at the project root. It executes `Puneetxp\CompilePhp\setup`:
   ```php
   use Puneetxp\CompilePhp\setup;
   require "./vendor/autoload.php";

   $setup = new setup(__DIR__);
   $setup->config();          // table_set + back-end generators + front-end generators + write()
   
   // Specialized operations:
   // $setup->migrate();      // Direct DB migration (drops DB first if "fresh": true)
   // $setup->sync();         // Introspects DB, auto-adds missing columns & FK constraints!
   // $setup->migratealter(); // Runs alter queries from database/mysql/alter/*.sql
   ```
3. **Database execution**:
   - `database/Migration.sql` contains combined table DDL, foreign keys, and role seed inserts.
   - For PostgreSQL: `psql -U $DBUSER -d $DBNAME -f database/Migration.sql`.
   - For MySQL: files consolidated in `database/mysql/{structure,relations,insert,alter}/`.
4. **PHP View Compilation**:
   - `php compile.php` executes `Puneetxp\CompilePhp\Compile\Compile`, parsing `<t-...>` HTML templates and `@props({...})` into PHP class components extending `\The\PageBase`.

---

## 2. Model JSON Schema Specification

```json
{
  "name": "client",                     // Singular model name (used for classes & types)
  "table": "clients",                   // Plural database table name
  "crud": {
    "isuper":  ["c","r","u","d","a","p","w"],
    "islogin": ["c","r","u","a","w"],
    "ipublic": ["r","a"],
    "roles":   { "executive": ["r","a"] }
  },
  "enable": 1,                          // Adds enable TINYINT(1) DEFAULT 1; generates toggle() in frontend
  "additional": ["slug","seo","delete"],// Presets: slug (VARCHAR 255), seo (title + seo_description), delete (deleted_at)
  "default": ["id", "created_at", "updated_at"], // Table lifecycle columns override
  "unique": ["email", ["user_id", "client_code"]], // Single & composite unique keys
  "data": [
    { "name": "name",   "mysql_data": "varchar(255)", "datatype": "string" },
    { "name": "email",  "mysql_data": "varchar(255)", "datatype": "string", "default": "NULL" },
    { "name": "status", "mysql_data": "varchar(20)",  "datatype": "string", "sql_attribute": "NOT NULL DEFAULT 'draft'" },
    { "name": "price",  "mysql_data": "decimal(10,2)","datatype": "number", "default": "0.00" },
    { "name": "notes",  "mysql_data": "text",         "datatype": "string", "default": "NULL" },
    { "name": "tags",   "mysql_data": "text[]",       "datatype": "array",  "default": "NULL" },
    { "name": "meta",   "mysql_data": "jsonb",        "datatype": "json",   "default": "NULL" }
  ],
  "relations": {
    "user": { "name": "user_id", "key": "id", "table": "users" }
  }
}
```

### A. CRUD Operations
- `c`: **Create** (`POST /`, status 201)
- `r`: **Read single** (`GET /{id}`)
- `u`: **Update** (`PUT /{id}` or `PATCH /{id}`)
- `d`: **Delete** (`DELETE /{id}`)
- `a`: **Read all** (`GET /`, supports `?latest=<updated_at>` delta sync)
- `w`: **Where filter** (`POST /where` with `{ filters }`)
- `p`: **Upsert / Batch** (`POST /upsert` or `PUT /`)

### B. Relations (3 Valid Formats)
1. **Simple String Array (Default 1:N convention)**:
   `"relations": ["user", "farm"]`
   Automatically creates `user_id BIGINT UNSIGNED NOT NULL` and `farm_id BIGINT UNSIGNED NOT NULL`, appends foreign keys, and configures ORM relationships.
2. **Object Array with Alias and Nullability**:
   `"relation": [{"name": "category", "alias": "service_category_id", "default": "NULL"}]`
   or multiple relations to the same table:
   `"relation": [{"name": "product", "alias": "primary_product"}, {"name": "product", "alias": "secondary_product"}]`
3. **Explicit Keyed Map (Recommended for enterprise / predefined `data` schemas)**:
   ```json
   "relations": {
     "crop": { "name": "crop_id", "key": "id", "table": "crops" },
     "farmer": { "name": "farmer_id", "key": "id", "table": "users" }
   }
   ```
   If the foreign key column (e.g. `crop_id`) is already declared in `"data"`, `explicitRelation()` binds directly to it without creating duplicate columns.

### C. Default Rules (`default` at 3 Levels)
1. **Table-Level Lifecycle (`defaultsetup`)**:
   Controls automatic system columns for the table. Defaults to `["id", "created_at", "updated_at"]`.
   - `id`: `BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT` (MySQL) or `BIGSERIAL PRIMARY KEY` (PostgreSQL), `fillable: false`.
   - `created_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL`, `fillable: false`.
   - `updated_at`: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL`, `fillable: false`.
   - Overrides:
     - `["id", "created_at"]`: Immutable event logs or append-only ledgers.
     - `["updated_at", "id"]`: Active session / state tables (e.g. `active_role.json`).
     - `["id"]`: Lean pivot / bridge tables without timestamp columns.
2. **Column-Level Default & Nullability**:
   - `"default": "NULL"` or `"default": null`: Generates `DEFAULT NULL`, TypeScript `T | null`, and Python `T | None = None`.
   - `"default": 0`, `"default": 1`, `"default": "'draft'"`: Sets SQL default value.
   - Any column without `"default": "NULL"` and without explicit `NULL` in `sql_attribute` is forced to `NOT NULL`.
3. **Relation-Level Foreign Key Nullability**:
   - `"relation": [{ "name": "client", "default": "NULL" }]`: Marks the auto-generated foreign key column as nullable (`DEFAULT NULL`).

### D. Built-in Schema Presets (`additional` & `enable`)
- `"enable": 1` or `"enable": true`: Injects `enable TINYINT(1) DEFAULT 1` (`datatype: 'number'`).
- `"additional": ["slug"]`: Injects `slug VARCHAR(255) NOT NULL`.
- `"additional": ["seo"]`: Injects `title VARCHAR(255) DEFAULT NULL` and `seo_description LONGTEXT DEFAULT NULL`.
- `"additional": ["delete"]`: Injects `deleted_at TIMESTAMP DEFAULT NULL`. Triggers soft-delete behavior in Deno and ORM services (`update({ deleted_at: new Date() })`).

### E. Model Types (`type`)
- Standard database table (default when omitted).
- `"type": { "name": "photo", "version": { "thumb": { "width": 200, "quality": 80 }, "large": { "width": 800, "quality": 90 } } }`:
  In PHP backend, generates image upload handler using `FileAct` and automated multi-size WebP resizing via `Img::webpImage()`.
- `"type": { "name": "file" }`: Generates binary file upload handling.

### F. Unique Constraints (`unique`)
- Single column: `"unique": ["email"]`
- Composite columns: `"unique": [["user_id", "crop_id"]]`
- Generates `UNIQUE KEY <name> (<cols>)` in MySQL and `CONSTRAINT <name> UNIQUE ("<cols>")` in PostgreSQL.

---

## 3. Database Engines & Schema Synchronization

### PostgreSQL Support (`"postgresql": true` in `config.json`)
- Native data type conversions:
  - `varchar(N)` → `VARCHAR(N)`
  - `decimal(M,D)` → `DECIMAL(M,D)`
  - `vector(N)` → `vector(N)` (PostgreSQL `pgvector` support)
  - `bigint` / `bigint unsigned` → `BIGINT`
  - `int` / `integer` → `INTEGER`
  - `tinyint(1)` → `SMALLINT`
  - `timestamp` → `TIMESTAMP`
  - `date` → `DATE`
  - `text` / `longtext` → `TEXT`
  - `text[]` → `TEXT[]` (PostgreSQL array type)
  - `json` / `jsonb` → `JSONB`
  - `boolean` → `BOOLEAN`
- Attribute stripping: Removes MySQL-specific keywords (`UNSIGNED`, `AUTO_INCREMENT`, `COMMENT`). Converts `id` with auto-increment to `BIGSERIAL PRIMARY KEY`.
- Output: Emits unified `database/structure.sql`, `database/relation.sql`, `database/insert.sql`, and `database/Migration.sql`.

### MySQL Support (Default)
- Emits individual table files in `database/mysql/{structure,relations,insert,alter}/` plus root consolidated files.

### Schema Synchronization (`$setup->sync()`)
- Inspects live database via `information_schema.columns` and `information_schema.KEY_COLUMN_USAGE`.
- Automatically executes `ALTER TABLE ADD COLUMN` for any newly added schema columns.
- Automatically executes `ALTER TABLE ADD CONSTRAINT FOREIGN KEY` for missing foreign key constraints.

### Schema Deltas (`database/Model/Additional/*.json`)
- Additional table extensions placed in `database/Model/Additional/*.json` are read by `$setup->add_table()`.
- Automatically generates `database/mysql/alter/<name>_alter.sql` with `ADD COLUMN IF NOT EXISTS` and merges attributes into memory.

---

## 4. Backend Generators

### A. Python / FastAPI (`pythonset.php`)
- Target directory: `python/app/`
- Architecture:
  - `app/models/<snake>.py`: Pydantic model (`BaseModel`) and request input schema (`<Model>Input`) with all fields optional and server-managed fields excluded.
  - `app/orm/<snake>.py`: ActiveRecord `Model` subclass with explicit `fillable` array and lazy-loading `relations` map using lambda imports (`lambda: __import__('app.orm.<module>', fromlist=['<Class>']).<Class>`).
  - `app/services/<snake>_service.py`: Service class extending `CrudService` with singleton getter.
  - `app/api/<scope>/<model>/<model>.py`: FastAPI `APIRouter` controllers:
    - `isuper`: Guarded by `dependencies=[Depends(get_current_admin)]`.
    - `islogin` & custom roles: Enforces `owner=current_user` scoping (`current_user=Depends(get_current_active_user)`).
  - `app/api/routers.py`: Auto-aggregates `all_routers` list for clean mounting in `app/main.py`.
  - Implicit namespace packages (PEP 420, no `__init__.py` clutter).

### B. Deno (`denoset.php`)
- Target directory: `deno/App/`
- Architecture:
  - `App/Model/<Name>.ts`: Subclasses `Model<T>` from `@puneetxp/the`.
  - `App/controller/<Role>/<Name>Controller.ts`: Static CRUD methods (`all`, `where`, `show`, `store`, `update`, `upsert`, `delete`).
  - Soft delete: Sets `deleted_at: new Date()` when model specifies `additional: ["delete"]`; exposes `perma_delete` for `isuper`.
  - Routing: `App/routes/<Role>.ts` exporting route arrays with roles. Supports `param: "URLPatternResult"` or `param: "string[]"`.

### C. PHP (`phpset.php`)
- Target directory: `php/App/`
- Architecture:
  - `App/Model/<Name>.php`: Subclasses `The\Model` with `$nullable`, `$fillable`, `$relations`.
  - `App/Controller/<Role>/<Role><Name>Controller.php`: REST controller methods.
  - Photo / file processing: Built-in `Img::webpImage` and `FileAct` for automatic multi-size thumbnailing.
  - Routes: `php/Routes/pre/api/<Role>.php` compiled to `Routes/web.php` via `php php/set.php`.

### D. .NET / C# (`dotnetset.php`)
- Target directory: `dotnet/`
- Generates C# class models in `dotnet/Models/<Name>.cs` and ASP.NET Core `[ApiController]` controllers in `dotnet/Controllers/<Name>Controller.cs`.

### E. Go / Gin (`golangset.php`)
- Target directory: `go/`
- Generates Go structs with `json:"..."` tags in `go/models/<name>.go` and Gin controller handlers in `go/controllers/<name>_controller.go`.

### F. Java / Spring Boot (`javaspringset.php`)
- Target directory: `spring/`
- Generates JPA entities (`@Entity`, `@Table`, Lombok `@Data`) in `spring/.../model/<Name>.java`, Spring Data JPA repositories in `repository/<Name>Repository.java`, and `@RestController` in `controller/<Name>Controller.java`.

---

## 5. Frontend Generators

### A. SolidJS (`solidset.php`)
- Target directory: `solidjs/src/shared/`
- Architecture:
  - `Interface/Model/<Name>.ts`: TypeScript interfaces with nullability mapping (`json` → `any`, `array` → `string[]`, `vector` → `number[]`).
  - `Service/Services.ts`: Instantiates typed `ModelService<T>`:
    ```typescript
    export const CropService = (new ModelService<Crop>())
      .seTable("crop")
      .seturl("/islogin/crop/");
    ```
    Preserves hand-written re-exports across regenerations (`export * from "./Weather"`).
  - `run.ts`: Central initializer executing `Service.checkinit()`, caching into IndexedDB on `isLogin()` and purging with `indexdb.The_clearData()` on logout.

### B. Angular (`angularset.php`)
- Target directory: `angular/src/app/shared/`
- Architecture:
  - `Service/Model/<Name>.service.ts`: Angular `@Injectable` service with RxJS observables (`name$`), delta-sync via `?latest=`, and toggle method for `enable`.
  - `Ngxs/State/<Name>.state.ts` & `Ngxs/Action/<Name>.action.ts`: Full NGXS State and Action declarations (`Set`, `Add`, `Edit`, `Delete`, `Upsert`).
  - `Form/Validation/<Name>.ts`: Reactive Form validation definitions (`Create<Name>Form`, `Update<Name>Form`) with `Validators.required` accurately computed based on column nullability.
  - `Service/run.service.ts`: Initialization service with timeouts.
  - Patches `angular.json` with custom assets and output paths.

### C. Vue (`vueset.php`)
- Target directory: `vuets/src/shared/`
- Architecture:
  - `Store/Model/<Name>.js`: Pinia store (`defineStore`) with getters, mutation actions (`addItem`, `removeItem`, `editItem`, `upsertItem`), and HMR support (`import.meta.hot`).
  - `Service/Model/<Name>.js`: REST service invoking Pinia store methods.

---

## 6. HTML Component Compiler (`Puneetxp\CompilePhp\Compile`)

- Source files: `src/Compile/Compile.php`, `htmlParser.php`, `phpCompile.php`.
- Compiles custom HTML components into PHP class components extending `\The\PageBase`.
- Syntax:
  - Components: `<t-component-name>`, `<t-php.if>`, `<t-php.for>`.
  - Props declaration: `@props({"condition": false, "child": false})`.
  - Templating: `{{ $expression }}` compiled to `<?= $expression ?>`.
  - Directives: `@foreach($items as $item) ... @endforeach`.

---

## 7. Configuration (`config.json`)

```json
{
  "fresh": false,
  "postgresql": true,
  "back-end": ["python"],
  "front-end": ["solidjs"],
  "env": {
    "dbhost": "localhost",
    "dbuser": "postgres",
    "dbpwd": "password",
    "dbname": "cropsense_db",
    "port": "5432"
  },
  "table": {
    "crop": false,
    "user": false
  }
}
```

- **`postgresql: true`**: Switches generator to PostgreSQL dialect (`BIGSERIAL`, `JSONB`, `vector`, `TEXT[]`).
- **`fresh: true`**: Drops and recreates database on migration.
- **`table` map**: Controls code overwriting. Setting `"crop": false` or `"crop": true` protects custom controller implementations from being overwritten. To force regeneration of a controller, delete its key from `table`.

---

## 8. Development Protocol & Best Practices

1. **Schema is the Single Source of Truth**: Always edit `database/Model/<name>.json`. Never manually modify generated models, DDL, or routers.
2. **Execute Full Pipeline**:
   ```bash
   ./pipeline.sh generate        # Runs setup.php
   ./pipeline.sh test-backend    # Verifies Python ORM & core tests
   ./pipeline.sh build-frontend   # Verifies TypeScript types & Vite build
   ./pipeline.sh check           # Full 5-point verification across all stacks
   ```
3. **Additive Schema Modifications**: Never drop or destructively rename existing columns in production tables. Add new fields with `"default": "NULL"` or sensible defaults.
4. **Ownership & Security**:
   - Every user-facing table must have an owner column (e.g. `user_id`, `farmer_id`, `created_by`) or be explicitly registered in `ownership.py` (`SHARED_READ`).
   - All `/islogin/` endpoints automatically enforce row-level ownership. Admin-only endpoints belong strictly in `isuper`.
