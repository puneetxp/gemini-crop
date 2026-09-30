# `the_lib`: PHP runtime (Composer `puneetxp/the`)

This is the source for PHP ≥ 8.2 apps, in namespace `The\` under `the_lib/src/`. Generated app code lives in `php/App` (namespace `App\`). The reference app is **intaxing23** (PHP + Angular).

## 1. Request flow
```text
.htaccess (RewriteRule ^(.*) /index.php) → php/index.php → new The\Route($route) → Controller::method(...$params)
```
```php
require_once __DIR__ . '/env.php';            // define()s generated from config.json → env (rewritten by php_set())
require_once __DIR__ . '/additionalenv.php';  // $_ENV, editable via /api/env (isuper)
require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/Routes/web.php';     // compiled by `php php/set.php`
new Route($route);
```
- `Route` starts the session using the `secure`, `sslhost`, `httponly` and `samesite` constants.
- `$_POST['_method']` overrides the HTTP verb.
- `$_POST['_action']` holds a batch of `{url, method, data}` requests and returns one JSON map.
- When the matched route has `islogin`, the router checks, in order: the guards, then the session, then `roles` against `Sessions::roles()` using `array_intersect`.
- The handler receives each `.+` path segment as a positional argument, and its return value is echoed.
- The development server needs a router script, because it ignores `.htaccess`: `php -S localhost:8000 -t public public/index.php`.

## 2. Routes (nested arrays, compiled by `The\compile\RouteCompile`)
There is **no chained `(new Route())->get()` API.** Routes are arrays in `php/Routes/pre/`. Run `php php/set.php` after every change; it writes `Routes/web.php`.
```php
$routes = [
  ["path" => "api", "child" => [
    ...$inotlogin,                        // POST/GET /login, POST /register, /googleauth/.+, /facebookauth/.+
    $ipublic,                             // /ipublic/<model>
    ["islogin" => true, "child" => [$isuper, ...$ienv, ...$iauth, $islogin]],  // $iauth = /logout, /auth/profile
  ]],
  ...$public, $login, ...$auth,           // server-rendered views
];
```
Route keys:
- `path`: a segment. Use `.+` for a parameter.
- `method`: defaults to `GET`.
- `handler`: `[Class::class, "m"]`.
- `islogin`, `roles`, `guard` (a list of callables), `child`, `group` (keyed by verb).
- `crud`: `["class" => X::class, "crud" => [letters]]`.

`path`, `islogin`, `roles` and `guard` are inherited by children. **`roles` and `guard` only run when `islogin` is true.**

| Letter | Verb and path | Handler |
|---|---|---|
| a | GET `/model` (supports `?latest=`) | `all()` |
| r | GET `/model/.+` | `show($id)` |
| c | POST `/model` | `store()` |
| w | POST `/model/where` | `where()` |
| u | **PATCH** `/model/.+` | `update($id)` |
| p | **PUT** `/model` | `upsert()` |
| d | DELETE `/model/.+` | `delete($id)` |

Generated files:
- `php/Routes/pre/api/<Role>.php`: `Isuper.php` (with `roles: ["isuper"]`), `Islogin.php`, `Ipublic.php`, and `I<role>.php` for custom roles.
- Controllers in `php/App/Controller/<Role>/<Role><Name>Controller.php`.

Apps add their own route files as well. intaxing23 has `Inotlogin.php`, `IsloginAdd.php`, `Ipaytm.php`, `Iexecutive.php` and `Imanager.php`, and it splices custom routes into `$isuper['child']` in `web.php`. Preserve these when editing.

**Template history:** templates up to compile-php 0.2.24 had the typo `"ilogin" => true` and kept login in `$iauth`, which left `/api/env` and `/api/isuper` open. Newer templates use the layout shown above.

## 3. Generated controller
```php
namespace App\Controller\Isuper;
use App\Model\Role;

class IsuperRoleController {
    public static function all() {
        if (isset($_GET["latest"])) return Role::wherec([["updated_at", ">", $_GET["latest"]]])->get();
        return Role::all();
    }
    public static function show($id)   { return Role::find($id); }
    public static function store()     { return Role::create($_POST)->getInserted(); }
    public static function update($id) { Role::where(["id" => [$id]])->update($_POST); return Role::find($id); }
    public static function upsert()    { return Role::upsert(json_decode($_POST["roles"]))->getsInserted(); }
}
```
- A model returned from a controller is echoed as JSON (via `__toString`).
- **Customised controllers:** keep the model's key in `config.json` → `table`. Any value protects it, because the check is `isset`. Delete the key to regenerate the controller.

## 4. Model (`The\Model`)
Generated models declare `$table`, `$name`, `$model` (the columns), `$fillable`, `$nullable` and `$relations`.
```php
User::all(); User::find(5); User::find("a@b.c", "email");                  // static
User::where(["enable" => [1], "id" => [1, 2]])->get();                      // values are ARRAYS → IN (...)
User::wherec([["created_at", ">", "2026-01-01"]])->get();                   // [[col, op, val]]
User::where([...])->andwhere([...])->orwhere([...])->andWhereC([[...]])->orWhereC([[...]]);
->get()  ->getnull()  ->first(["name"])  ->count()  User::all()->paginate(1, 25)   // also ?page= & ?pageItems=
User::create($data)->getInserted(); User::insert($rows); User::upsert($rows)->getsInserted();
User::where(["id" => [5]])->update($data)->first(["name"]);                // update() executes immediately
(new User)->toggle(["id" => [5]], "enable");                                // instance method
User::delete(["id" => [5]]);
Invoice::find(1)->with(["client", "user"])->sort();                         // eager load, then nest
Book::all()->with([["invoice" => ["client"]]])->sort();                     // nested relations
The\DB::raw($sql, $bind);
```
- **`where()` and `update()` silently drop keys that aren't columns** (`Req::get($this->model, …)`).
  - A misspelled column in `where()` turns into **no WHERE**.
  - `update()` without a where updates every row.
- `sort()` orders children by their `sort` column when that column is fillable.

## 5. Auth and sessions
- **`Auth::login`:** reads `email` and `password`. Passwords are compared with `hash('sha3-256', …)` (no salt). On success it calls `Sessions::create()` and returns `{name, email, id, roles}`.
- **`Auth::register`:** reads `name`, `email` and `password`. Returns 422 `{"email":"Email Already Taken"}` if the email exists.
- **`Auth::status`, `Auth::logout`:** also available.
- **`isuper` means user id 1** (`Sessions::roles()`). Every other role comes from `active_roles` (user_id, role_id) → `roles.name`. Don't change this table shape or its meaning; live apps depend on it.
- **`SocialAuth::g_auth($token)`, `SocialAuth::f_auth($token)`:** Google and Facebook sign-in.
- **Known bug, security (up to 0.1.304):** `Auth::profile()` and `profileupdate()` use `where(["user_id" => …])`. That column doesn't exist, so profile returns the first user and profileupdate updates **all** users. The fix is `["id" => [$_SESSION['user_id']]]` and allowing only `name`, `phone` and `email`. Ask the user before editing `the_lib`.
- **Known bug:** on a wrong password, `Auth::login` doesn't return its `Response::why()` result, so the client gets 404 "User Not Found".

## 6. Helpers
```php
Req::only(["name", "email"]); Req::one("name"); Req::get($keys, $data); Req::array($keys, $rows);
Response::json($d); Response::not_found($m); Response::not_authorised($m); Response::unprocessable($m); Response::bad_req($m); Response::NotLogin();
FileAct::init($_FILES["photo"])->public("brand")->fileupload($_FILES["photo"], "logo");   // → [..., "public" => "/storage/brand/logo.png"]
Img::webpImage(source: $src, destination: $dst, x: 300, quality: 80);
(new Mail)->to(["a@b.c"])->subject("Hi")->message("<b>Hello</b>")->send();                 // to() takes an array
```
Uploads go to `../storage`. Symlink them into the web root with `ln -s ../storage/public public/storage`.
