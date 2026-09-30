# SolidJS frontend: generated services, ModelService and IndexedDB

The generator is `compile-php/src/Class/solidset.php`, selected with `front-end: ["solidjs"]`. There are two reference apps, and they use **different** `ModelService` implementations. Pick the one that matches the app's backend.

| App | Backend | Base class | HTTP | Router |
|---|---|---|---|---|
| **apac-genaiacademy-c2** (`/Users/waseemakram/Documents/apac-genaiacademy-c2/solidjs`) | Python/FastAPI under `/api/v1` | `src/shared/Service/ModelService.ts` | `src/lib/api-client.ts` (Bearer token, retry, cache) | `@solidjs/router` 0.15 |
| **the_billing** (`/Users/waseemakram/Documents/the_billing/solidjs`) | Deno `the@0.0.2`, cookie session | `src/shared/Service/Service.ts` | `thelib.ts` `JFetch`/`JGetFetch` | `the-solid-router` |

## 1. What the generator writes (`solidjs/src/shared/`)
| File | Contents |
|---|---|
| `Interface/Model/<Name>.ts` | The interface for the table: `id`, `created_at`, `updated_at`, the columns and the `<rel>_id` keys |
| `Service/Services.ts` | One singleton per model, as below |
| `run.ts` | `tables: string[]` (the IndexedDB stores) and `class run` (hydrate after login, clear after logout) |

```ts
import { ModelService } from "./ModelService";      // "./ModelService" if that file exists, else "./Service"
export const FarmService = (new ModelService<Farm>())
    .seTable("farm")
    .seturl("/islogin/farm/");
export * from "./Custom";                           // hand-added re-export lines are KEPT on regeneration
```

- **Every service URL is `/islogin/<model>/`.** Don't change this in the generator: each app's `ModelService` or `apiClient` adds its own prefix, which is `/api/v1` in apac. An earlier attempt to emit `/api/islogin/` would have broken apac, so it was reverted.
- **Interfaces, `Services.ts` and `run.ts` are regenerated on every run.** Put custom logic in separate service files (apac: `src/services/*.service.ts`, `src/stores/*`) and re-export them from `Services.ts` with `export * from`.
- **The generator does not write `ModelService`, `Store.ts` or `indexdb.ts`.** They're app code; copy them from a reference app.

## 2. `Stores<T>` (`Service/Store.ts`, same idea in both apps)
- It holds a Solid `createStore({ data: T[] })` and mirrors every write to IndexedDB.
- **Reading state:** `allstate()`, `keyById()`, `findState(id)`, `getState(id, key?)`.
- **Changing state:** `setstate`, `upsertstate` (merge by `id`), `addstate`, `updatestate`, `delstate`.
- Components read `XService.allstate()` inside JSX. The store is reactive, so no extra signals are needed.

## 3. `ModelService<T>`: pick the matching implementation
| Method | apac → Python backend | the_billing → Deno 0.0.2 |
|---|---|---|
| `all()` | Hydrates from IndexedDB, then `GET base` every time (full list; the backend is owner-scoped) | Hydrates from IndexedDB, then `GET url` the first time, then `GET url?latest=<newest updated_at, sv-SE format>` (delta sync) |
| `get(id)` | GET `base+id` | GET `url/id` |
| `create(body)` | POST `base` | POST `url` |
| `update(id, body)` | **PUT** `base+id` | **POST** `url/id` |
| `upsert(rows)` | Per row: PUT if it has an `id`, else POST | **PATCH** `url` |
| `where(filter)` | GET the list, then **filters on the client** | POST `url/where` |
| `del(id)` | DELETE `base+id` | DELETE `url/id` |
| Extras | `bulkImport()` → POST `base + "bulk_ai_import"` | none |

The HTTP verbs must match the backend runtime:

| Backend | update | upsert |
|---|---|---|
| PHP `the_lib` | PATCH `/id` | PUT `/` |
| Deno `the@0.0.2` | POST `/id` | PATCH `/` |
| Deno `@puneetxp/the@0.1.x` | PATCH or PUT `/id` | PATCH or PUT `/` |
| Python | PUT `/id` | POST `/upsert` |

A wrong verb shows up as a 404 or 405, not as a clear error.

**URL mapping in apac:** `get base()` turns legacy `"api/<table>"` or bare `"<table>"` into `/islogin/<table>/`, and custom paths such as `"api/soil/health"` into `/soil/health/`. Absolute paths and paths starting with `/` are used as they are, with a trailing slash added. `apiClient` then adds `baseURL`, which is `VITE_API_URL + "/api/v1"` and falls back to `http://localhost:8000/api/v1`.

## 4. Auth and HTTP
### apac: `src/lib/api-client.ts`, default export `apiClient`
- **Requests:** `apiClient.get/post/put/delete<T>(path, config)`, returning `{ data }`.
- **Auth:** attaches `Authorization: Bearer <access_token>` from localStorage. On a 401 it calls `POST {baseURL}/auth/refresh-token` with `{username, refresh_token}` and retries.
- **Reliability:** 30 s timeout, 3 retries and a 5-minute GET cache. `ModelService` passes `{ cache: false }`.
- **Login and hydration:**
  - Sign-in is done with Firebase (`src/lib/firebase.ts`).
  - `shared/guard/all.ts` `isLogin()` checks that both `access_token` and `refresh_token` are in localStorage.
  - `run.ts` hydrates every service after login, or runs `indexdb.The_clearData()` after logout.

### the_billing: `thelib.ts`
- `Fetch`, `JFetch` and `JGetFetch` rely on the session cookie (`PHPSESSID`).
- A 401 triggers `LoginService.check()`.
- The hand-written `src/shared/api.ts` wraps the book-scoped endpoints: `bookUrl(path)` = `/api/islogin/book/${activeBookId()}/${path}`.
- The Vite dev proxy forwards `/api` to Deno on `:9000` with `rewrite: p => p.replace(/^\/api/, "")`, just as nginx does in production.

## 5. IndexedDB (`shared/indexdb.ts`)
- Methods: `The_putSomeData(table, rows)`, `The_setData`, `The_delSomeData(table, id)`, `The_getAllData`, `The_getall<T>(table)` and `The_clearData()`.
- **apac:** DB `rural_farming_db`. It opens without a fixed version and bumps the version when a table from `run.ts` → `tables` is missing, so new models add their store automatically. `checkinit()` catches IndexedDB failures and carries on without the cache.
- **the_billing:** DB `intax`, `dbVersion = 1`.
- **Always clear IndexedDB on logout**, or the next user sees the previous user's cached rows.

## 6. Routing
- **apac:** `@solidjs/router`, with `<Router root={App}>` and flat `<Route path component>` entries in `src/index.tsx`. The `...Wrapped` components add layout and auth.
- **the_billing:** `the-solid-router`, with nested `<Route>` entries that take a `guard` prop. `new run().set` guards the root route; `notLogin` and `isLogin` guard the auth pages.

## 7. Conventions and checks
- Use the generated interfaces for types. Don't declare model types again by hand.
- apac-only features: i18n (`src/i18n`, with `npm run i18n:check`, which runs before every build), vitest (`npm test`) and `tsc --noEmit` (`npm run type-check`).
- **Build commands:**
  - apac: `npm run build`. It runs `prebuild`, the i18n check.
  - the_billing: `npx vite build`. It has about 26 existing TypeScript errors in legacy input components, `thelib.ts` and `_user/add/category.tsx`.
- **After a generator change,** regenerate a copy of the app and `diff -r` it before and after. `Services.ts` and `run.ts` must only change where you intended.
