# AgriSense Premier — Stitch Design System Specification

## Project Metadata
- **Stitch Project ID**: `projects/9950740652342953015`
- **Title**: CropSense AI - Smart Agriculture Platform
- **Device Type**: Mobile & Desktop Responsive
- **Primary Color**: Emerald Forest (`#065f46` / `#004532`)
- **Secondary Color**: Harvest Amber (`#d97706` / `#fe932c`)
- **Tertiary Color**: Mint Telemetry (`#10b981` / `#6ffbbe`)
- **Background**: Bone Cream (`#faf9f5`)
- **Surface**: Warm White (`#ffffff`)
- **Typography**: Plus Jakarta Sans
- **Iconography**: Material Symbols Outlined (with `opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200`)

---

## Token Reference Table

| Role | Token Key | Hex Value | Semantic Usage |
| :--- | :--- | :--- | :--- |
| **Primary** | `primary` | `#004532` | Critical action buttons, key brand headers |
| **Primary Container** | `primary-container` | `#065f46` | Active navigation tabs, top badges |
| **On Primary** | `on-primary` | `#ffffff` | Text on primary containers |
| **Primary Fixed** | `primary-fixed` | `#a6f2d1` | Subtle chip backgrounds, tags |
| **Secondary** | `secondary` | `#904d00` | Alert metrics, mandi prices, active bids |
| **Secondary Container** | `secondary-container` | `#fe932c` | Attention flags, pending contracts |
| **Tertiary** | `tertiary` | `#00462e` | Healthy plant flags, optimal moisture |
| **Tertiary Container** | `tertiary-container` | `#006041` | AI vision tag backgrounds |
| **Tertiary Fixed** | `tertiary-fixed` | `#6ffbbe` | Live telemetry glowing dots |
| **Surface** | `surface` | `#faf9f5` | Page background canvas |
| **Surface Lowest** | `surface-container-lowest` | `#ffffff` | Elevated cards, forms, panels |
| **Surface Low** | `surface-container-low` | `#f4f4f0` | Sub-cards, table headers |
| **Surface High** | `surface-container-high` | `#e9e8e4` | Hover states, pill containers |
| **Outline** | `outline` | `#6f7973` | Subtitles, disabled states, borders |
| **Outline Variant**| `outline-variant` | `#bec9c2` | Divider lines, card outlines |
| **On Surface** | `on-surface` | `#1b1c1a` | High-contrast body text |
| **On Surface Variant** | `on-surface-variant` | `#3f4944` | Secondary text, inactive nav items |

---

## Responsive Grid Standard
- **Mobile (< 640px)**: 1-column cards, `p-4`, sticky top header with hamburger/back, fixed bottom nav dock (`max-w-lg mx-auto`).
- **Tablet (640px - 1024px)**: 2-column bento grid, sidebar collapses to icon-rail or top drawer.
- **Desktop (≥ 1024px)**: 12-column bento grid, persistent `w-64` / `w-72` sticky sidebar, bottom dock hidden (`lg:hidden`).
