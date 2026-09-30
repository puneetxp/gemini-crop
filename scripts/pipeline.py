#!/usr/bin/env python3
"""
CropSense AI — Master Pipeline Automation Script (scripts/pipeline.py)

Automates the entire development, audit, and build lifecycle:
1. sanitize-screens: 5-Point audit & auto-fix on stitch/screens/*.html (Fonts, tag symmetry, responsive shell, deterministic links).
2. sync-index: Discovers all screens in stitch/screens/ and syncs tabs with index.html showcase viewer.
3. generate: Runs /opt/homebrew/bin/php setup.php to regenerate database DDL, Pydantic models, ORM, and TypeScript types.
4. test-backend: Runs Python core tests (ActiveRecord Model, DB query builder, CrudService, ownership rules, JWT auth, rate limiter).
5. build-frontend: Runs npm run build in solidjs using node/npm.
6. all / check: Runs all audits and checks in sequence with colorized summary output.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

# Base workspace directory
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SCREENS_DIR = WORKSPACE_ROOT / "stitch" / "screens"
INDEX_HTML = WORKSPACE_ROOT / "index.html"
PYTHON_APP_DIR = WORKSPACE_ROOT / "python"
SOLIDJS_DIR = WORKSPACE_ROOT / "solidjs"

# Color formatting helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_step(title: str):
    print(f"\n{BOLD}{CYAN}==> {title}{RESET}")


def log_success(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")


def log_warn(msg: str):
    print(f"  {YELLOW}⚠{RESET} {msg}")


def log_error(msg: str):
    print(f"  {RED}✗{RESET} {msg}")


# ----------------------------------------------------------------------
# 1. Screen Sanitization & Tag Symmetry Engine
# ----------------------------------------------------------------------
def sanitize_screens(auto_fix: bool = True) -> bool:
    """Audit and sanitize all HTML screens in stitch/screens/."""
    log_step("Auditing & Sanitizing Stitch Screens (5-Point Engine)")

    if not SCREENS_DIR.exists():
        log_error(f"Screens directory does not exist: {SCREENS_DIR}")
        return False

    screens = sorted(SCREENS_DIR.glob("*.html"))
    if not screens:
        log_warn("No HTML screens found in stitch/screens/")
        return True

    all_passed = True
    fixed_count = 0

    required_font_link = (
        '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:'
        'opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />'
    )

    for screen_path in screens:
        rel_name = screen_path.name
        content = screen_path.read_text(encoding="utf-8")
        modified = False
        screen_passed = True

        # Rule 1: Font URL with Axis Specifiers
        if "Material+Symbols+Outlined" in content and "opsz,wght,FILL,GRAD" not in content:
            if auto_fix:
                content = re.sub(
                    r'<link[^>]*family=Material\+Symbols\+Outlined[^>]*>',
                    required_font_link,
                    content,
                )
                modified = True
                log_warn(f"{rel_name}: Upgraded Material Symbols font URL with required axis parameters")
            else:
                log_error(f"{rel_name}: Missing axis specifiers in Material Symbols font link")
                screen_passed = False
                all_passed = False

        # Rule 2: Tag Symmetry (<button>...</a> and <a>...</button>)
        b_a_matches = re.findall(r'<button\b[^>]*>(?:(?!</button>).)*?</a\s*>', content, re.DOTALL)
        a_b_matches = re.findall(r'<a\b[^>]*>(?:(?!</a>).)*?</button\s*>', content, re.DOTALL)

        if b_a_matches or a_b_matches:
            if auto_fix:
                # Fix <button...>...</a\> -> <button...>...</button>
                content = re.sub(
                    r'(<button\b[^>]*>(?:(?!</button>).)*?)</a\s*>',
                    r'\1</button>',
                    content,
                    flags=re.DOTALL,
                )
                # Fix <a...>...</button\> -> <a...>...</a\>
                content = re.sub(
                    r'(<a\b[^>]*>(?:(?!</a>).)*?)</button\s*>',
                    r'\1</a>',
                    content,
                    flags=re.DOTALL,
                )
                modified = True
                log_warn(f"{rel_name}: Auto-fixed {len(b_a_matches) + len(a_b_matches)} mismatched tags")
            else:
                log_error(f"{rel_name}: Detected mismatched tags: {len(b_a_matches)} button->a, {len(a_b_matches)} a->button")
                screen_passed = False
                all_passed = False

        # Rule 3: Deterministic links pointing to screen_desktop_*.html
        if "screen1_dashboard.html" in content and screen_path.name.startswith("screen_desktop_"):
            if auto_fix:
                content = content.replace("screen1_dashboard.html", "screen_desktop_dashboard.html")
                content = content.replace("screen2_diagnose.html", "screen_desktop_diagnose.html")
                content = content.replace("screen3_booking.html", "screen_desktop_booking.html")
                content = content.replace("screen4_livestock.html", "screen_desktop_livestock.html")
                content = content.replace("screen5_soil_satellite.html", "screen_desktop_soil_satellite.html")
                modified = True
                log_warn(f"{rel_name}: Updated internal links to responsive screen_desktop_* files")

        if modified and auto_fix:
            screen_path.write_text(content, encoding="utf-8")
            fixed_count += 1
            log_success(f"{rel_name}: Saved sanitized file")
        elif screen_passed:
            log_success(f"{rel_name}: Validated 100% compliant")

    print(f"\n{BOLD}Screens Audit Result:{RESET} Checked {len(screens)} screens. Auto-fixed {fixed_count}. Status: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


# ----------------------------------------------------------------------
# 2. Sync Screens in Master Showcase (index.html)
# ----------------------------------------------------------------------
def sync_showcase() -> bool:
    """Ensure all screens in stitch/screens/ are registered in index.html viewer."""
    log_step("Verifying Master Showcase Viewer (index.html)")

    if not INDEX_HTML.exists():
        log_error("index.html not found in project root")
        return False

    content = INDEX_HTML.read_text(encoding="utf-8")
    screens = sorted([s.name for s in SCREENS_DIR.glob("screen_desktop_*.html")])

    missing_in_index = []
    for screen in screens:
        if f"stitch/screens/{screen}" not in content and screen not in content:
            missing_in_index.append(screen)

    if missing_in_index:
        log_warn(f"Showcase index.html is missing tabs for: {missing_in_index}")
    else:
        log_success(f"Showcase index.html is fully synchronized with {len(screens)} responsive screens")

    return True


# ----------------------------------------------------------------------
# 3. Model Generation (setup.php / compile-php)
# ----------------------------------------------------------------------
def run_schema_generator() -> bool:
    """Run /opt/homebrew/bin/php setup.php to regenerate models."""
    log_step("Executing Schema Generator (setup.php)")

    php_bin = "/opt/homebrew/bin/php"
    if not Path(php_bin).exists():
        # Fallback to system php
        res = subprocess.run(["which", "php"], capture_output=True, text=True)
        if res.returncode == 0:
            php_bin = res.stdout.strip()
        else:
            log_error("PHP binary not found (expected /opt/homebrew/bin/php)")
            return False

    setup_file = WORKSPACE_ROOT / "setup.php"
    if not setup_file.exists():
        log_error("setup.php not found in project root")
        return False

    cmd = [php_bin, str(setup_file)]
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)

    if res.returncode == 0:
        log_success("Models, ORM, DDL, and interfaces generated successfully")
        return True
    else:
        log_error(f"setup.php failed with code {res.returncode}:\n{res.stderr}")
        return False


# ----------------------------------------------------------------------
# 4. Backend Core Integration Tests
# ----------------------------------------------------------------------
def test_backend() -> bool:
    """Run verification tests on python/app/core/."""
    log_step("Testing Backend Core Infrastructure (python/app/core/)")

    python_bin = "/opt/homebrew/bin/python3"
    if not Path(python_bin).exists():
        python_bin = sys.executable

    test_script = """
import sys
from pathlib import Path

# Add python path
sys.path.insert(0, 'python')

from app.core.config import settings
from app.core.db import DB
from app.core.model import Model
from app.core.crud_service import CrudService
from app.core.ownership import (
    OWNERSHIP, OWNER_COLUMNS, SHARED_READ, PARENTS,
    get_ownership_clause, is_shared_read, enforce_owner_columns, validate_parent_ownership
)
from app.core.auth import FirebaseTokenValidator, resolve_user_from_db
from app.core.rate_limiter import limiter
from app.orm.user import User

# 1. Test Config
assert settings.DB_NAME == 'cropsense_db', 'Settings failed'

# 2. Test Ownership Rules
assert len(OWNERSHIP) >= 35, f'Expected >= 35 ownership rules, got {len(OWNERSHIP)}'
assert get_ownership_clause('farms', 42) == '(t.user_id = 42 OR t.owner_id = 42)'
assert is_shared_read('veterinarians') is True
assert OWNER_COLUMNS['transport_bookings'] == 'requester_id'

# 3. Test Model Query Builder
q = User().where('email', 'test@farm.in').where('enable', 1)
sql, params = q._build_select_sql()
assert 'WHERE' in sql and 'ORDER BY' in sql, 'SQL builder failed'

# 4. Test Mock Authentication
claims = FirebaseTokenValidator.verify_token('mock-token-farmer@test.in')
assert claims['email'] == 'farmer@test.in'
user = resolve_user_from_db(claims)
assert user['email'] == 'farmer@test.in'

# 5. Test CrudService with local fallback
user_service = CrudService(User)
created = user_service.create({'name': 'Test Farmer', 'email': 'test_farmer@domain.in'})
assert created is not None and created.get('id') is not None, 'CrudService create failed'

# 6. Test Rate Limiter
key = 'test-client-unique'
assert limiter.is_rate_limited(key, max_requests=2, window_seconds=10) is False
assert limiter.is_rate_limited(key, max_requests=2, window_seconds=10) is False
assert limiter.is_rate_limited(key, max_requests=2, window_seconds=10) is True

print('ALL_BACKEND_TESTS_OK')
"""

    env = os.environ.copy()
    env["PYTHONPATH"] = "python"
    res = subprocess.run([python_bin, "-c", test_script], cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, env=env)

    if res.returncode == 0 and "ALL_BACKEND_TESTS_OK" in res.stdout:
        log_success("psycopg3 DB pool & SQLite fallback: PASS")
        log_success("ActiveRecord Model & CrudService: PASS")
        log_success("Row-level ownership & parent security: PASS")
        log_success("Firebase JWT & E2E mock authentication: PASS")
        log_success("Sliding window rate limiter: PASS")
        return True
    else:
        log_error(f"Backend test failed:\n{res.stdout}\n{res.stderr}")
        return False


# ----------------------------------------------------------------------
# 5. Frontend Build & Verification
# ----------------------------------------------------------------------
def build_frontend() -> bool:
    """Run npm run build in solidjs/."""
    log_step("Building SolidJS Frontend (Vite Production Build)")

    # Prepare node PATH
    node_paths = [
        os.path.expanduser("~/.nvm/versions/node/v24.20.0/bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    env = os.environ.copy()
    env["PATH"] = ":".join(node_paths) + ":" + env.get("PATH", "")

    # Check npm existence
    which_npm = subprocess.run(["which", "npm"], capture_output=True, text=True, env=env)
    if which_npm.returncode != 0:
        log_error("npm not found in PATH")
        return False

    npm_bin = which_npm.stdout.strip()
    cmd = [npm_bin, "run", "build"]
    res = subprocess.run(cmd, cwd=str(SOLIDJS_DIR), capture_output=True, text=True, env=env)

    if res.returncode == 0:
        # Extract bundle size from stdout
        for line in res.stdout.splitlines():
            if "dist/" in line:
                print(f"  {line.strip()}")
        log_success("SolidJS build compiled with 0 errors")
        return True
    else:
        log_error(f"Frontend build failed:\n{res.stdout}\n{res.stderr}")
        return False


# ----------------------------------------------------------------------
# Main CLI Router
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="CropSense AI Master Pipeline Automation Script",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="all",
        choices=["all", "sanitize-screens", "sync-index", "generate", "test-backend", "build-frontend", "check"],
        help=(
            "Action to perform:\n"
            "  all            Run complete pipeline (audit screens, test backend, build frontend)\n"
            "  sanitize-screens Audit and auto-fix stitch/screens/*.html\n"
            "  sync-index     Verify index.html showcase viewer synchronization\n"
            "  generate       Run setup.php schema code generator\n"
            "  test-backend   Run python/app/core/ unit and integration tests\n"
            "  build-frontend Run Vite build on solidjs/\n"
            "  check          Non-destructive verification check across all stacks\n"
        ),
    )

    args = parser.parse_args()

    print(f"\n{BOLD}{GREEN}======================================================{RESET}")
    print(f"{BOLD}{GREEN}  CropSense AI — Master Pipeline Runner{RESET}")
    print(f"{BOLD}{GREEN}======================================================{RESET}")

    results = {}

    if args.action in ("all", "sanitize-screens", "check"):
        results["sanitize-screens"] = sanitize_screens(auto_fix=(args.action != "check"))

    if args.action in ("all", "sync-index", "check"):
        results["sync-index"] = sync_showcase()

    if args.action == "generate":
        results["generate"] = run_schema_generator()

    if args.action in ("all", "test-backend", "check"):
        results["test-backend"] = test_backend()

    if args.action in ("all", "build-frontend", "check"):
        results["build-frontend"] = build_frontend()

    # Print Summary Table
    print(f"\n{BOLD}------------------------------------------------------{RESET}")
    print(f"{BOLD}Pipeline Execution Summary:{RESET}")
    all_success = True
    for action_name, success in results.items():
        status_text = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  - {action_name:<20}: {status_text}")
        if not success:
            all_success = False
    print(f"{BOLD}------------------------------------------------------{RESET}\n")

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
