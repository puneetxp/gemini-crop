# Angular: generated code plus the `the-angular` library

The reference app is intaxing23, whose `angular/` folder is a symlink to `angular16intaxing` on the author's machine.
- **npm package:** `the-angular` 0.0.13. It needs Angular 21, `@angular/material` 21, `@ngxs/store` 21 and rxjs 7.8.
- **Source:** `the-angular/`. The entry point is `public-api.ts`; the root `index.ts` is stale and not used.
- **Legacy:** `the-angular-material` is the Angular 16 predecessor. Its build is broken.

## 1. Generated code (`front-end: ["angular"]`, `angular/src/app/shared/`)
| Path | Contents |
|---|---|
| `Interface/Model/<Name>.ts` | An interface for the table |
| `Service/Model/<Name>.service.ts` | The API service, wired to NGXS and IndexedDB |
| `Ngxs/State/<Name>.state.ts`, `Ngxs/Action/<Name>.action.ts` | The actions `Set`, `Add`, `Edit`, `Upsert` and `Delete` |
| `Form/Validation/<Name>.ts` | `Create<name>Form` and `Update<name>Form`, which map fields to validators. The name uses the model's lowercase name, e.g. `CreatebrandForm`. |
| `db/tables.ts`, `Service/run.service.ts` | The IndexedDB tables and the start-up hydration |

`config.json` → `angular.outputPath` is patched into `angular.json`. It can be a string, or an object such as intaxing23's `{ "base": "../intaxing/public_html", "browser": "" }`. An asset of `"src/storage"` is symlinked to `storage/public`.

Service API:
```ts
this.brandService.prefix("isuper").all();   // url = /api/isuper/brand (default /api/brand)
brands$ = this.brandService.allState();     // Observable<Brand[]>
```
| Method | HTTP | Store action |
|---|---|---|
| `all()` | GET `url` the first time, then GET `url?latest=<newest updated_at>` | `Set` / `Upsert` |
| `fresh()` | GET `url` | `Set` |
| `get(id)` | GET `url/id` (returns an Observable) | none |
| `create(v)` | POST `url` | `Add` |
| `update(id, v)` | **PATCH** `url/id` | `Edit` |
| `upsert(rows)` | **PUT** `url`, body `{ <table>: rows }` | `Upsert` |
| `del(id)` | DELETE `url/id` | `Delete` |
| `toggle(id)` | flips `enable`; only generated when the model has `enable` | `Edit` |
| `allState()`, `getState(id, key)`, `array()` | none (reads the store) | none |

These verbs match the PHP runtime and Deno 0.1.x. Deno `the@0.0.2` expects POST for update.

## 2. the-angular library
Import from the package root; `exports` only allows `"."`:
```ts
import { FormDynamicComponent, TableMaterialComponent, SidenavComponent, setformbase, predefined, initservice, IndexedDBService, AuthService } from "the-angular";
```
**Exported components:**
- `the-form-dynamic`, `the-input-dynamic`
- `the-table-material`
- `the-sidenav` (`[menus]`), `the-footer`, `the-page-title`, `the-skeleton`, `the-sort`
- `the-upload-image`, `the-login-dialog`
- the not-found and not-allowed pages

These exist in the source but are **not exported:** the header, `the-confirm`, `the-paginate`, `the-select-image(s)`, the guards, and more.

```html
<the-table-material [table_mat$]="brandService.allState()" [columnsToDisplay]="['name','enable']"
  [isfilter]="true" [isPaginate]="true" [PageSize]="25" [isEdit]="true" [isDelete]="true" [isEnable]="true"
  (edit)="edit($event)" (delete)="brandService.del($event)" (enable)="brandService.toggle($event)"></the-table-material>
```
```ts
// Form.ts
export const Form = [
  { key: "name", label: "Name", controlType: "textbox", row: "col-span-2" },
  { key: "type", label: "Type", controlType: "dropdown", options: [{ key: "a", value: "A" }] },
  predefined.slug,            // static fields: seoform (array), _name, slug, phone, email, description, user, client, gstn, service_plan…
  predefined.enable(true),    // enable is a function
];
// component
inputs = setformbase(Form, [CreatebrandForm, {}]);
```
```html
<the-form-dynamic [inputs]="inputs" [formClass]="'grid grid-cols-4 gap-2'" (formOutput)="brandService.create($event)" />
```
- **`controlType` values:** `textbox`, `textarea`, `password`, `hidden`, `dropdown`, `select`, `dropdownautocomplete`, `chipselect`, `checkbox`, `toggle`, `datepicker`, `date` and `photo`.
- **Validators:** each field takes `validator: ValidatorFn[]`, not `validators: ['required']`.

**Services and state:**
- `AuthService`:
  - `login()` sends POST `/api/login`. Any 2xx counts as success and dispatches `SetLogin`; on an error it sets `error = e.error`.
  - `logout()` sends GET `/api/logout`.
  - Google and Facebook sign-in call `/api/googleauth/:token` and `/api/facebookauth/:token`.
- `LoginState`, with selectors `getLogin` and `isLogin`, and the actions `SetLogin` / `DeleteLogin`.
- `IndexedDBService`: `The_putSomeData`, `The_getAllData` and `The_delSomeData`.
- `initservice(services, prefix)` calls `prefix(prefix).all()` on each service.
- Others: `DialogService`, `DynamicFormService`, `FormDataService`, `ImageService`, `LoginService`.

**Build:** `npm run build` (ng-packagr), which outputs `dist/the-angular`. The package is published by CI from `main`.
