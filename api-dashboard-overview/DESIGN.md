# 优丁租户工作台 — 设计规范 (DESIGN.md)

> Stitch-optimized semantic design system for YouDing foreign trade SaaS dashboard
> Generated: 2026-07-21 | Version: 1.0.0

---

## 1. Visual Theme & Atmosphere

**Density:** Daily App Balanced (5/10)
**Variance:** Offset Asymmetric (6/10)
**Motion:** Fluid CSS with Spring Physics (6/10)

A dark-tech industrial dashboard with restrained elegance. The atmosphere is like a well-lit control room for global trade — clinical precision meets warm mint accents. Glass-morphism surfaces create depth through layered translucency, while subtle radial gradients add atmospheric warmth to the deep charcoal canvas. Every interaction feels weighty and deliberate, like operating precision instruments.

**Design Philosophy:**
- Dark-first: Deep charcoal backgrounds with mint green accent
- Glass surfaces: Frosted cards with backdrop-filter blur
- Data-dense but breathable: Generous padding despite content richness
- Functional beauty: Every visual element serves a purpose

---

## 2. Color Palette & Roles

### Core Palette
| Token | Hex | Role |
|-------|-----|------|
| **Canvas Night** | `#0c0d10` | Primary background, deep canvas |
| **Card Glass** | `rgba(21,22,26,0.85)` | Card surfaces with transparency |
| **Popover Deep** | `#1c1d22` | Dropdown/popover backgrounds |
| **Muted Panel** | `#1a1b20` | Input fields, muted sections |
| **Whisper Border** | `rgba(255,255,255,0.06)` | Subtle structural lines |
| **Soft Border** | `rgba(255,255,255,0.04)` | Table dividers, subtle separations |

### Text Hierarchy
| Token | Hex | Role |
|-------|-----|------|
| **Primary Text** | `#f0f2f5` | Headings, important labels |
| **Card Text** | `#e4e6eb` | Card content, secondary emphasis |
| **Muted Text** | `#8b8fa0` | Descriptions, metadata, timestamps |

### Accent & State Colors
| Token | Hex | Role |
|-------|-----|------|
| **Mint Primary** | `#4a9b8c` | CTAs, active states, focus rings |
| **Mint Light** | `rgba(74,155,140,0.1)` | Hover backgrounds, subtle highlights |
| **Success Green** | `#10b981` | Positive states, completed actions |
| **Warning Amber** | `#f59e0b` | Caution states, pending items |
| **Danger Red** | `#ef4444` | Error states, destructive actions |
| **Info Blue** | `#3b82f6` | Informational badges, links |

### Forbidden Colors
- ❌ `#000000` (Pure black) — Use `#0c0d10` or Off-Black
- ❌ Neon purples, electric blues — No AI cliché aesthetics
- ❌ Oversaturated accents — Keep saturation below 80%

---

## 3. Typography Rules

### Font Stack
```
Primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
Mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace
CJK: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif
```

### Type Scale
| Class | Size | Weight | Line Height | Letter Spacing | Use |
|-------|------|--------|-------------|----------------|-----|
| `.brand-h1` | 1.75rem (28px) | 700 | 1.2 | -0.02em | Page titles |
| `.brand-h2` | 1.3125rem (21px) | 600 | 1.3 | -0.01em | Section headings |
| `.brand-h3` | 1.0625rem (17px) | 600 | 1.4 | normal | Card titles |
| `.brand-h4` | 0.9375rem (15px) | 600 | 1.4 | normal | Subsection titles |
| `.brand-body` | 0.875rem (14px) | 400 | 1.6 | normal | Body content |
| `.brand-body-sm` | 0.8125rem (13px) | 400 | 1.5 | normal | Compact body |
| `.brand-caption` | 0.75rem (12px) | 500 | 1.4 | normal | Labels, metadata |
| `.brand-mono` | 0.8125rem (13px) | 400 | 1.5 | normal | Code, numbers |

### Typography Anti-Patterns
- ❌ No generic serif fonts (Times New Roman, Georgia)
- ❌ No massive hero text — hierarchy through weight, not size
- ❌ No `LABEL // YEAR` lazy formatting

---

## 4. Component Stylings

### Cards (`.panel`)
```css
.panel {
  background: rgba(21,22,26,0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  transition: all 0.3s ease-out;
}

.panel:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}
```

### Buttons
- **Primary:** Mint background (`#4a9b8c`), white text, tactile -1px push on active
- **Secondary:** Ghost outline, mint text, transparent background
- **Hover:** Subtle background lightening, no neon glows

### Badges (`.badge`, `.tag`)
- Rounded pill shape (6px radius)
- State-colored backgrounds at 15% opacity
- Compact padding: 2px 8px

### Data Tables
- Striped rows with subtle alternating backgrounds
- Hover highlight with mint-tinted background
- Sticky headers with glass-morphism blur

### Inputs
- Label above input (not floating)
- Focus ring in mint primary color
- Helper text below, error text in red

---

## 5. Layout Principles

### Grid System
- **Sidebar:** 232px fixed width, glass-morphism background
- **Main Content:** Fluid width with 24px padding
- **Max Content Width:** 1400px centered
- **Card Grids:** CSS Grid with auto-fit, minmax(280px, 1fr)

### Spacing Scale
| Token | Value | Use |
|-------|-------|-----|
| `--spacing-xs` | 4px | Tight gaps |
| `--spacing-sm` | 8px | Component internal padding |
| `--spacing-md` | 16px | Card padding, section gaps |
| `--spacing-lg` | 24px | Main content padding |
| `--spacing-xl` | 32px | Section separators |

### Responsive Rules
- **Desktop (≥1024px):** Full sidebar + fluid content
- **Tablet (768-1023px):** Collapsed sidebar, 2-column grids
- **Mobile (<768px):** Single column, hidden sidebar

---

## 6. Radius Scale

| Token | Value | Use |
|-------|-------|-----|
| `--radius-sm` | 6px | Badges, small buttons |
| `--radius-md` | 10px | Inputs, compact cards |
| `--radius-lg` | 14px | Cards, panels, modals |
| `--radius-xl` | 20px | ⚠️ DEPRECATED — Do not use |

**Rule:** Maximum radius is 14px (`--radius-lg`). No 20px+ rounded shapes.

---

## 7. Motion & Interaction Philosophy

### Timing Functions
```css
/* Standard transitions */
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);  /* For bouncy effects */
--ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);       /* For subtle movements */

/* Duration scale */
--duration-fast: 150ms;
--duration-normal: 300ms;
--duration-slow: 500ms;
```

### Animation Patterns

#### Card Entrance (`.ujCardEnter`)
```css
@keyframes ujCardEnter {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```
- Use for: Card mounting, section reveals
- Duration: 300ms
- Stagger: 50ms delay between siblings

#### Progress Shimmer (`.ujShimmer`)
```css
@keyframes ujShimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```
- Use for: Loading states, progress bars
- Duration: 2.5s infinite loop

#### Hover Lift
```css
.panel:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3);
  border-color: rgba(74,155,140,0.15);
}
```
- Use for: Interactive cards, clickable elements
- Duration: 300ms ease-out

#### Spring Bounce (for playful interactions)
```css
.spring-bounce {
  animation: springBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes springBounce {
  0% { transform: scale(0.8); opacity: 0; }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); opacity: 1; }
}
```
- Use for: Modals, popovers, emphasis moments

### Performance Rules
- ✅ Animate ONLY `transform` and `opacity`
- ❌ NEVER animate `top`, `left`, `width`, `height`
- ✅ Use `will-change: transform` for animated elements
- ✅ Isolate CPU-heavy animations in `<Client>` components (Next.js)

---

## 8. Glass-Morphism System

### Base Glass Effect
```css
.glass-surface {
  background: rgba(21,22,26,0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
}
```

### Glass Variants
| Variant | Background | Blur | Border |
|---------|------------|------|--------|
| Card | `rgba(21,22,26,0.85)` | 20px | `rgba(255,255,255,0.06)` |
| Sidebar | `rgba(17,18,21,0.95)` | 20px | `rgba(255,255,255,0.04)` |
| Modal | `rgba(12,13,16,0.9)` | 24px | `rgba(255,255,255,0.08)` |
| Popover | `rgba(28,29,34,0.95)` | 16px | `rgba(255,255,255,0.06)` |

---

## 9. Shadow System

```css
/* Subtle elevation */
--shadow-sm: 0 2px 8px rgba(0,0,0,0.2);

/* Card hover */
--shadow-md: 0 8px 24px rgba(0,0,0,0.25);

/* Modal/overlay */
--shadow-lg: 0 12px 40px rgba(0,0,0,0.3);

/* Heavy elevation */
--shadow-xl: 0 20px 60px rgba(0,0,0,0.4);
```

**Rule:** No neon outer glows. Shadows are tinted to background hue.

---

## 10. Anti-Patterns (Banned)

### Visual Anti-Patterns
- ❌ Pure black `#000000` — Use Off-Black or Zinc-950
- ❌ Neon/outer glow shadows
- ❌ Oversaturated accent colors (saturation > 80%)
- ❌ Generic serif fonts in dashboards
- ❌ Emojis in UI (use Lucide icons instead)
- ❌ Custom mouse cursors
- ❌ Overlapping elements — clean spatial separation always

### Layout Anti-Patterns
- ❌ 3-column equal card grids — Use asymmetric layouts
- ❌ Centered Hero sections — Use left-aligned or split
- ❌ Horizontal scroll on mobile
- ❌ `h-screen` — Use `min-h-[100dvh]`

### Animation Anti-Patterns
- ❌ Linear easing — Always use ease-out or spring
- ❌ Animating `top/left/width/height` — Transform only
- ❌ Generic circular spinners — Use skeletal loaders
- ❌ Bouncing chevrons, "Scroll to explore" text

### Content Anti-Patterns
- ❌ Generic names ("John Doe", "Acme Corp")
- ❌ Fake round numbers ("99.99% uptime")
- ❌ AI copywriting clichés ("Elevate", "Seamless", "Unleash")
- ❌ `LABEL // YEAR` formatting
- ❌ Broken Unsplash links — Use picsum.photos or SVG

---

## 11. Component Library Reference

### KPI Card Pattern
```html
<div class="kpi-card" style="background:linear-gradient(135deg, [color] 0%, [color-darker] 100%);">
  <div class="kpi-card__icon"><!-- Lucide icon --></div>
  <div class="kpi-card__label">指标名称</div>
  <div class="kpi-card__value">1,234</div>
  <div class="kpi-card__trend">+12%</div>
</div>
```

### Data Table Pattern
```html
<table class="data-table">
  <thead>
    <tr>
      <th>列标题</th>
      <!-- ... -->
    </tr>
  </thead>
  <tbody>
    <tr class="data-table__row">
      <td>数据</td>
      <!-- ... -->
    </tr>
  </tbody>
</table>
```

### Badge Pattern
```html
<span class="badge badge--success">已完成</span>
<span class="badge badge--warning">处理中</span>
<span class="badge badge--danger">失败</span>
<span class="badge badge--info">信息</span>
```

---

## 12. Design Token CSS Variables

```css
:root {
  /* Colors */
  --color-background: #0c0d10;
  --color-foreground: #f0f2f5;
  --color-card: #15161a;
  --color-card-foreground: #e4e6eb;
  --color-primary: #4a9b8c;
  --color-muted: #1a1b20;
  --color-muted-foreground: #8b8fa0;
  --color-border: #26272e;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-info: #3b82f6;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
  --shadow-md: 0 8px 24px rgba(0,0,0,0.25);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.3);

  /* Motion */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
}
```

---

## 13. Audit Results & Improvements Needed

> **Last audit: 2026-07-21 | All blocking issues resolved**

### ✅ Passing (8/8)
- Dark theme consistency across all 17 pages
- Glass-morphism card pattern used consistently
- Mint primary `#4a9b8c` used as single accent
- No pure black `#000000` found
- No neon glow effects
- Transform/opacity animations dominant (467+ occurrences)
- Lucide icons used consistently (no emojis)
- **Spring Physics easing added** — `cubic-bezier(0.34, 1.56, 0.64, 1)` injected into all 17 pages (card entrance, hover transitions, perpetual micro-interactions)
- **Radius XL fixed** — `--radius-xl` reduced from 20px to 14px (backward-compatible alias)
- **Motion tokens added** — `--ease-out`, `--ease-spring`, `--ease-smooth`, `--duration-fast/normal/slow` in `colors_and_type.css`
- **Perpetual micro-interactions added** — `ujPulse` (2s infinite) and `ujFloat` (3s infinite) keyframes available via `.uj-pulse` and `.uj-float` classes

### ⚠️ Warnings (Non-Blocking)
1. **Inter font in premium context** — `wangcai-chat-widget.html` uses Inter directly. Consider using Geist or Satoshi for the chat widget mascot context.
2. **Hardcoded colors** — 18 files contain hardcoded hex values outside `<style id="theme-vars">`. Should be replaced with CSS variables (non-blocking for canvas rendering).

### ❌ Critical Issues (Blocking)
*None — all blocking issues resolved on 2026-07-21*

### 📋 Recommended Future Improvements
1. Standardize all hardcoded colors to CSS variables (cosmetic)
2. Consider replacing Inter with Geist/Satoshi for premium feel (cosmetic)

---

## 14. File Structure

```
api-dashboard-overview/
├── DESIGN.md                    ← This file
├── colors_and_type.css          ← Design tokens & typography
├── orchestration-summary.json   ← Build metadata
├── validation-report.json       ← Quality gate results
├── api-dashboard-overview.design ← Canvas project file
├── assets/                      ← Static assets
└── pages/                       ← 17 HTML pages
    ├── dashboard-overview.html
    ├── today-workbench.html
    ├── copilot-dashboard.html
    ├── traffic-board.html
    ├── inquiry-management.html
    ├── inquiry-queue.html
    ├── sales-dashboard.html
    ├── customer-finder.html
    ├── attribution.html
    ├── content-distribute.html
    ├── publish-queue.html
    ├── fulfillment-queue.html
    ├── billing.html
    ├── onboarding.html
    ├── wangcai-chat-widget.html
    ├── seo-overview.html
    └── geo-visibility.html
```

---

*This DESIGN.md serves as the single source of truth for YouDing's tenant dashboard design system. All new pages and components should adhere to these specifications.*
