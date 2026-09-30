# `The.DotNet.Lib` (.NET), plus the status of Go and Spring

**Generation is not wired in.** `"dotnet"`, `"golang"` and `"spring"` in `config.json` → `back-end` do nothing today:
- `compile-php` `setup::config()` never calls `dotnetset`, `golangset` or `javaspringset`.
- `src/template/{dotnet,go,spring}` don't exist.
- The generators only write stubs. .NET controllers return `Ok()`, Go uses placeholder Gin handlers, and Spring uses `javax.persistence`, which Spring Boot 3 doesn't support.
- None of them use the runtime libraries below, and they ignore `crud` roles.

Only enable these generators if the user asks. Then:
1. Wire them into `config()`.
2. Call the generating method; the constructor alone does nothing.
3. Add the templates.

## the_dotnet (`the_dotnet/Lib/The.DotNet.Lib.csproj`)
- `net10.0`, namespace `The.DotNet.Lib`.
- Uses ASP.NET Core, Identity plus EF Core Sqlite, and JWT Bearer 10.0.9.
- Not on NuGet. Reference it with `dotnet add reference ../the_dotnet/Lib/The.DotNet.Lib.csproj`.

```csharp
IDB db = new DB(new SqliteConnection("Data Source=app.db"));   // ADO.NET; "?" placeholders → @p0, @p1…

public class Product : Model { public Product(IDB db) : base(db) { Table = "products"; Name = "product"; } }
var m = new Product(db);
m.Find(1); m.All().Items; m.Where(new Dictionary<string, object> { { "enable", 1 } }).Items;  // list value → IN (?,…)
m.Wherec(sql, placeholders); m.Count(); m.Paginate(1, 25); m.Create(data); m.Update(data, where); m.Delete(where);
m.Join(...); m.With(...).Sort();   // eager loading like PHP

// Auth = ASP.NET Identity + JWT (NOT the SHA256/db-based API older docs show)
await Auth.Register(userManager, email, password);
var r = await Auth.Login(userManager, signInManager, email, password);   // { token, email }
```

Gotchas:
- **Returns:** every statement runs through `ExecuteReader`, so `Update` and `Delete` return 0 rather than the number of rows affected.
- **Names aren't parameterized:** table and column names are interpolated into the SQL. Never pass user input as a column name.
- **JWT key:** it is hard-coded as `"SuperSecretKey123ForTestingPurposesOnly"`. Replace it before any real use.
- **No roles:** there is no role or namespace support; `isuper`, `islogin` and `ipublic` don't exist here.

**Sample: `the_dotnet_api`** (not a git repo):
- Exposes `POST api/auth/register` and `POST api/auth/login` with `{Email, Password}`.
- Uses Sqlite `users.db`.
- `dotnet run` serves on http://localhost:5034.

## the_go and the_spring
Both are skeletons from 2026-01-11.

**the_go:**
- Packages: `utils/{sqlbuilder,model,auth,session,response,file,mail}`.
- There's no `go.mod`, and `DB` has no implementation.
- `auth.Login` and `auth.Register` are placeholders.
- `session` is a global map, which isn't request-safe.

**the_spring:**
- Package `com.puneetxp.lib`.
- There's no `pom.xml` or `build.gradle`.
- `Model.DB` is an interface with no implementation.
- `Auth` is a placeholder.
- `Session` is a static map.
- `Response` wraps output as `{data: …}`.

Treat both as starting points for a port, not usable runtimes.
