# `the_deno`: Deno runtime (JSR `@puneetxp/the`)

The current release is **`jsr:@puneetxp/the@0.1.16`** (`the_deno/deno.json`). The_billing (INTAX) still pins **`https://deno.land/x/the@0.0.2/mod.ts`**. Check `deno/dep.ts` before you write code, because the two versions differ.

## 1. Bootstrap
```ts
// deno/dep.ts: keep every runtime import here
export { compile_routes, compile_url_pattern, DB, hash, Model, response, Router, Session, setRole } from "jsr:@puneetxp/the@0.1.16";
export type { _Routes, relation, Route_Group_with } from "jsr:@puneetxp/the@0.1.16";

// deno/index.ts
setRole((await Role$().all()).items);                       // load the roles table once, before any session
Deno.serve({ port: 9000 }, async (req) =>
  (await new Router(routes, req).URLPattern()?.run()) ?? new Response("Not Found", { status: 404 }));

// deno/App/Routes/index.ts
export const routes = compile_url_pattern(compile_routes([
  { handler: Public.Home },
  { islogin: true, child: [...islogin, ...isuper] },
  ...Auth,
]));
```
- Run with `deno run --watch --allow-all --unstable-kv index.ts`. KV is required, because sessions live in Deno KV.
- The database connection comes from env or `deno/.env`: `DBHOST`, `DBUSER`, `DBPWD` and `DBNAME`. Version 0.1.x also reads `DBPORT`, `DBPOOL` and `DBSOCKET`.
- **Obsolete APIs (don't use them):**
  - `new Router(routes).route(req)`
  - `/.+` array params
  - `(req, params)` handlers
  - the deno.land/x `0.0.0.4.x` imports

## 2. Routes
Route fields:
- `path`: a URLPattern, e.g. `/:id` or `/book/:book_id/client`.
- `method`: defaults to GET.
- `handler(session, param)`.
- `islogin`, `guard: ((req) => Promise<false | string>)[]`, `roles`, `child`, `group`, and `crud: { class, crud: [letters] }`.

**Guards and roles only run when `islogin` is true** (inherited counts). Guards return `false` to allow the request, or a string to deny it.
```ts
static async show(session: Session, param: URLPatternResult) {
  const id = param.pathname.groups.id;
  const latest = new URL(session.req.url).searchParams.get("latest");
  const body = await session.req.json();             // raw Request = session.req
  return response.JSON((await Client$().find(id)).item, session);
}
```
| Letter | 0.1.x | 0.0.2 |
|---|---|---|
| a / r | GET `/` / GET `/:id` | same |
| c / w | POST `/` / POST `/where` | same |
| u | PATCH or PUT `/:id` | **POST `/:id`** |
| p | PATCH or PUT `/` | PATCH `/` |
| d | DELETE `/:id` + DELETE `/perma_delete/:id` (isuper) | DELETE `/:id` |

Differences in 0.1.x:
- The first matching route wins (in 0.0.2 the last one wins).
- Returns a real 404, and a 500 on exceptions.
- Adds CORS on every response, plus `response.OPTIONS(req)`.
- Supports `Authorization: Bearer` API keys (the `api_keys` table).
- The user with id 1 bypasses role checks.

Generated files:
- `App/Routes/Islogin.ts` exports `islogin`.
- `App/Routes/Isuper.ts` exports `isuper`, with `roles: ["isuper"]`.
- `App/Routes/<Role>.ts` for custom roles.
- Controllers in `App/Controller/<Role>/<Name>Controller.ts`.

**These files are rewritten on every `deno_set()`.** the_billing has hand-edited `Islogin.ts` (nested book routes) and `Isuper.ts`, so save them before you regenerate.

Generated `delete` handlers soft-delete (`update({deleted_at})`) only when the model has `additional: ["delete"]`, and use `Model.delete` otherwise. compile-php 0.2.24 and earlier always soft-deleted.

## 3. Session
- **Access:**
  - `session.Login`: `{ id, name, email, roles }`
  - `session.ActiveLoginSession`: `{ books, book, session_id, expire, ip, agent, … }`
  - `session.req`
- **Login:** `session.startnew(user, activeRoles, books?, book?)`, then `response.JSONF(session.getLogin().Login, session.returnCookie())`.
- **Keep alive:** `session.reactiveSession()`, or respond with `response.JSONS`.
- **Logout:** `session.removeSession()`.
- **Cookie:** `PHPSESSID`, httpOnly. The domain comes from env `ssl`, plus env `samesite` and `secure`.
- **Bug in 0.0.2:** `SessionRoles` gives every user every role (`.filter` inside `.filter`). 0.1.x fixes it with `.some`. the_billing recomputes the roles in `withRealRoles()` in `AuthController.ts`; keep that workaround while it's on 0.0.2.
- `ActiveLoginSession.book` is always `books[0]`. Scope by the URL's `:book_id` instead.

## 4. Model
```ts
class Standard extends Model<Client> { constructor() { super("client", "clients", nullable, fillable, columns, { book: { table: "books", name: "book_id", key: "id", callback: () => Book$ } }); } }
export const Client$ = () => new Standard();          // current generator: factory (fresh query state per call)
// the_billing (older output): export const Client$ = new Standard();  → shared instance, call without ()
```
```ts
(await Client$().all()).items;  (await Client$().find(5)).item;
(await Client$().where({ book_id: [3] }).andWhereC([["updated_at", ">", latest]]).get()).items;
await Client$().create({...});        // 0.1.x sets .item; 0.0.2 needs .getInserted()
await Client$().where({ id: [5] }).update({...});   // update() without where() updates ALL rows
await Client$().upsert([...]); await Client$().delete({ id: [5] });
await (await Invoice$().where({ id: [1] }).get()).with("client");   // with() is async
```
- Results are on `.item` and `.items`. **There is no `.Item` or `del`.**
- 0.1.x adds `paginate`, `count`, `first`, `softDelete`, `withJoin`, `clone` and `toJSON`.

## 5. Responses
```ts
response.JSON(body, session?, status?, headers?)
response.JSONS(body, session?, status?, headers?)
response.JSONF(body, headers?, status?)
```

## 6. Per-tenant pattern (the_billing)
```ts
export async function ownedBook(session: Session, param: URLPatternResult): Promise<number | Response> {
  const book_id = Number(param.pathname.groups.book_id);
  if (!book_id) return response.JSON("Book is required", session, 400);
  const book = (await Book$.find(book_id)).item;
  if (!book || book.user_id != session.Login.id) return response.JSON("Not Your Book", session, 403);
  return book_id;
}
// controller: const book_id = await ownedBook(session, param); if (book_id instanceof Response) return book_id;
// then always filter: where({ id: [id], book_id: [book_id] })
```
- the_billing's routes are `/islogin/book/:book_id/{client,invoice,account,journal,journal_detail,asset,stock}`, plus `/islogin/server` (scoped per user) and `/isuper/*`.
- The Deno routes have **no `/api` prefix**. nginx strips it with `proxy_pass http://localhost:9000/;`, and the Vite dev proxy uses `rewrite: p => p.replace(/^\/api/, "")`.

## 7. Checks
Run `deno check index.ts`, or `npx -y deno check index.ts` when Deno isn't installed. the_billing's `deno check App/Routes/index.ts` already has about 23 errors in legacy files.
