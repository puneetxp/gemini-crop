---
name: stitch-to-code
description: >
  Convert Google Stitch designs into clean, responsive, production-ready frontend code (SolidJS/HTML)
  and backend schemas (FastAPI/PostgreSQL). Covers Stitch MCP ingestion, design preservation,
  HTML sanitization, responsive Tailwind transformation, SolidJS reactive component generation,
  and index showcase integration. Trigger whenever converting a Stitch screen, generating new screens
  with Stitch MCP, fixing broken Stitch HTML, or creating SolidJS components from Stitch prototypes.
---

# Stitch-to-Code: Production Design & Architecture Pipeline

A robust, automated pipeline to take raw Google Stitch screens and convert them into production-ready **SolidJS components**, **responsive preview screens**, and **FastAPI backend models** without corrupting or breaking design fidelity.

---

## 1. Directory Structure Convention

Never store raw or ad-hoc edited Stitch files in the project root. All Stitch assets must follow this strict structure:

```
stitch/
├── screens/                  # All standardized responsive & prototype HTML screens
│   ├── screen_desktop_dashboard.html
│   ├── screen_desktop_diagnose.html
│   ├── screen_desktop_booking.html
│   ├── screen_desktop_livestock.html
│   ├── screen_desktop_soil_satellite.html
│   ├── screen_desktop_strategy.html
│   ├── screen_desktop_auth.html
│   └── ...
├── specs/                    # Design tokens & Stitch project metadata
│   └── design_system.md      # "AgriSense Premier" theme tokens & constraints
└── prompts/                  # Text prompts used to generate Stitch screens
    ├── auth.prompt.txt
    ├── farm_register.prompt.txt
    └── ...
```

---

## 2. Ingestion & Generation via Stitch MCP

When a new screen needs to be designed:
1. **Target Project**: Always use Project ID `9950740652342953015` ("CropSense AI - Smart Agriculture Platform").
2. **Design System**: Use `AgriSense Premier` tokens (Emerald `#004532`, Amber `#fe932c`, Mint `#10b981`, Plus Jakarta Sans).
3. **Generate**:
   ```json
   {
     "projectId": "9950740652342953015",
     "prompt": "High-fidelity agricultural screen for...",
     "deviceType": "DESKTOP",
     "modelId": "GEMINI_3_8_FLASH"
   }
   ```
4. **Save Raw Output**: Save the untouched generated HTML directly to `stitch/screens/<screen_name>.html`.

---

## 3. The 5-Point Automated Sanitization Checklist

Raw Stitch outputs or edited files frequently develop subtle bugs. Every screen must pass this 5-point audit:

### Rule 1: Font URL with Axis Specifiers
Google Fonts requires the `opsz` axis parameter for Material Symbols Outlined; otherwise, Google Fonts returns empty CSS and icons render as blank text:
- **Mandatory Link**:
  ```html
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
  ```
- **Mandatory CSS Rule**:
  ```css
  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    display: inline-block;
    vertical-align: middle;
    line-height: 1;
  }
  ```

### Rule 2: HTML Tag Symmetry (No Tag Mismatches)
Never mix opening `<button>` with closing `</a>` or opening `<a>` with closing `</button>`.
Run this validation command to guarantee 0 tag mismatches:
```bash
python3 -c "
import glob, re
for f in sorted(glob.glob('stitch/screens/*.html')):
    with open(f) as fp: c = fp.read()
    b_a = len(re.findall(r'<button[^>]*>(?:(?!</button>).)*?</a\s*>', c, re.DOTALL))
    a_b = len(re.findall(r'<a[^>]*>(?:(?!</a>).)*?</button\s*>', c, re.DOTALL))
    assert b_a == 0 and a_b == 0, f'{f} has tag mismatches: {b_a}, {a_b}'
print('All stitch screens have 100% valid tag symmetry.')
"
```

### Rule 3: Universal Responsive Shell
Every screen must be responsive across **Mobile (390px)**, **Tablet (768px)**, and **Desktop (1440px)**:
- **Sidebar**: Must have `hidden lg:flex` (or `hidden md:flex`) so it collapses on mobile viewports.
- **Top Bar**: Must include a mobile view trigger/brand row for `< lg` viewports.
- **Bottom Navigation Dock**: Must be anchored with `lg:hidden fixed bottom-0 left-0 right-0 max-w-lg mx-auto w-full z-50`. Adding `left-0 right-0 max-w-lg mx-auto` prevents the dock from misaligning or stretching awkwardly on larger screens.

### Rule 4: Deterministic Cross-Links
Never leave dead `href="#"` or broken placeholder URLs. Wire all navigation items to valid screens:
- Dashboard: `screen_desktop_dashboard.html`
- AI Doctor: `screen_desktop_diagnose.html`
- Mandi & Booking: `screen_desktop_booking.html`
- Pashu Livestock: `screen_desktop_livestock.html`
- Soil & Satellite: `screen_desktop_soil_satellite.html`
- Annual Strategy: `screen_desktop_strategy.html`

### Rule 5: Design Token Fidelity
Surfaces must use `AgriSense Premier` tokens defined in `stitch/specs/design_system.md`:
- Canvas: `bg-background` (`#faf9f5`)
- Cards: `bg-surface-container-lowest` (`#ffffff`) with `border border-outline-variant/30`
- Primary brand: `bg-primary` (`#004532`) and `bg-primary-container` (`#065f46`)
- Alert metrics: `text-secondary` (`#904d00`) and `bg-secondary-container` (`#fe932c`)

---

## 4. SolidJS Component Conversion Workflow

To convert a sanitized Stitch screen into a production SolidJS component:

### Step 1: Create Component File
Create the component in `solidjs/src/pages/<Domain>/<PageName>.tsx`.

### Step 2: Extract Clean JSX
1. Keep Tailwind utility classes intact. In SolidJS, `class="..."` is native and preferred over `className`.
2. Wrap in `<div class="min-h-screen bg-background text-on-surface flex flex-col lg:flex-row">`.

### Step 3: Replace Mock Values with Reactive Signals & Stores
Convert static cards to reactive bindings:
```tsx
import { createSignal, createResource, For, Show } from "solid-js";
import { apiClient } from "../../lib/api-client";

export default function DiagnosticDashboard() {
  const [activePlot, setActivePlot] = createSignal("Plot A • Sharbati Wheat");
  const [diagnoses] = createResource(async () => {
    return await apiClient.get("/vision/diagnose-crop");
  });

  return (
    <div class="flex-1 p-6 space-y-6">
      <Show when={!diagnoses.loading} fallback={<div class="p-8 text-center text-outline">Loading Telemetry...</div>}>
        <For each={diagnoses()}>
          {(item) => (
            <div class="p-4 rounded-2xl bg-surface-container-lowest border border-outline-variant/30 shadow-xs">
              <h3 class="font-bold text-primary">{item.crop_name}</h3>
              <p class="text-xs text-outline">{item.status}</p>
            </div>
          )}
        </For>
      </Show>
    </div>
  );
}
```

### Step 4: Backend Schema Generation via `the-framework`
Whenever a screen introduces new persistent entities:
1. Define `database/Model/<name>.json`.
2. Run `/opt/homebrew/bin/php setup.php` in the workspace root.
3. Automatically generates:
   - `database/structure.sql` (PostgreSQL)
   - `python/app/models/<name>.py` (Pydantic)
   - `python/app/orm/<name>.py` (ORM)
   - `python/app/api/<scope>/<name>/<name>.py` (FastAPI)
   - `solidjs/src/shared/Interface/Model/<Name>.ts` (TypeScript)

---

## 5. Showcase Registration & Live Sync

Every newly created or updated screen must be registered in [index.html](file:///Users/waseemakram/Documents/gemini-crop/index.html):
1. Add the domain and filename to `screenMap` in `index.html`.
2. Add a navigation button in the `QUICK NAVIGATION BAR`.
3. Update [TASKS.md](file:///Users/waseemakram/Documents/gemini-crop/TASKS.md) to mark the task completed.
