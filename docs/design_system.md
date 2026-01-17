# Perplexica Design System (v2.0)

## 🎨 Design Philosophy
"Data-First, Distraction-Free."
Focused on legibility, trust (via visible sourcing), and fluid interaction. Inspired by modern search engines (Perplexity) but optimized for local 10TB+ datasets.

## 🌈 Color Palette (Tailwind Tokens)

### Theme: Dark Mode First
Perplexica is primarily a dark-mode interface.

| Token | Scoped Value (Dark) | Usage |
|-------|---------------------|-------|
| `bg-dark-primary` | `#0f1117` | Main background (Deep Space) |
| `bg-dark-secondary` | `#161b22` | Cards, Sidebar, Inputs |
| `border-dark-200` | `#21262d` | Subtle borders, dividers |
| `text-white` | `#f0f6fc` | Primary text (High contrast) |
| `text-white/70` | `#8b949e` | Secondary text, citations |
| `accent-blue` | `#58a6ff` | Links, Active States, Highlights |
| `status-green` | `#238636` | Success, "Verified" claims |
| `status-red` | `#f85149` | Error, "Refuted" claims |

### Light Mode (Secondary)
| Token | Scoped Value (Light) | Usage |
|-------|----------------------|-------|
| `bg-light-primary` | `#ffffff` | Main background |
| `bg-light-secondary` | `#f6f8fa` | Cards, Sidebar |
| `border-light-200` | `#d0d7de` | Borders |

## typography Typography
**Font Family:** `PP Editorial` (Headings), `Inter` / `System UI` (Body/UI)

| Scale | Size (px) | Weight | Usage |
|-------|-----------|--------|-------|
| `text-3xl` | 32 | Medium | User Queries, Major Headings |
| `text-xl` | 20 | Medium | Section Headers (Sources, Answer) |
| `text-lg` | 18 | Regular | Result Titles |
| `text-base` | 16 | Regular | Body Text, Answer Content |
| `text-sm` | 14 | Regular | Metadata, Citations, Captions |
| `text-xs` | 12 | Medium | Badges, Tags |

## 🧩 Core Components

### 1. Cards (Source/Media)
- **Style:** `bg-light-secondary/dark-bg-dark-secondary`
- **Border:** `border border-transparent hover:border-light-200/dark:border-dark-200`
- **Interaction:** Hover scales slightly or shows detailed tooltips.
- **Content:** Thumbnail (Left/Top) + Title + Domain/Path + Date.

### 2. Buttons
- **Primary:** `bg-black/white text-white/black rounded-full` (Action)
- **Secondary:** `bg-transparent border border-light-200/dark:border-dark-200` (Filter)
- **Icon-Only:** `text-black/70 dark:text-white/70 hover:bg-gray-100/80`

### 3. Inputs (Search)
- **Style:** Floating, heavy shadow in light mode, glow in dark mode.
- **Shape:** `rounded-full` (Global Search) or `rounded-xl` (Follow-up).

## ♿ Accessibility Standards
- **Contrast:** AA Standard minimum for text.
- **Focus Rings:** Visible `focus:ring-2` on all interactive elements.
- **ARIA:**
    - `aria-label` on all icon-only buttons.
    - `aria-expanded` on collapsible sections.
    - `role="status"` for loading states.

## 🛠️ Implementation Guide
Use `cn()` helper for className merging.
```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  "p-4 rounded-lg transition-colors",
  "bg-light-secondary dark:bg-dark-secondary",
  "hover:bg-light-secondary/80 dark:hover:bg-dark-secondary/80"
)} />
```
