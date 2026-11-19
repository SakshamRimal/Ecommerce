---
name: Design System
description: Use when defining tokens, typography, colors, layout primitives, reusable UI components, or accessibility standards.
---

# Design System

## When to use

- Initial visual language.
- Adding a reusable component.
- Reviewing visual consistency or accessibility.
- Dark mode / responsive work.

## Foundations

### Tokens

```css
:root {
  --color-bg: #ffffff;
  --color-fg: #111827;
  --color-muted: #6b7280;
  --color-border: #e5e7eb;
  --color-primary: #111827;
  --color-primary-fg: #ffffff;
  --color-danger: #b91c1c;
  --color-success: #047857;
  --radius-sm: 6px;
  --radius-md: 10px;
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --font-sans: ui-sans-serif, system-ui, sans-serif;
  --text-sm: 0.875rem; --text-base: 1rem; --text-lg: 1.125rem;
  --shadow-card: 0 1px 2px rgb(0 0 0 / 0.06), 0 1px 3px rgb(0 0 0 / 0.1);
}
```

- Use a token, never a raw hex/px in feature code.
- Support `prefers-color-scheme` if dark mode is in scope.
- 4/8 px spacing scale.

### Typography

- One sans family; 3–4 sizes per page.
- Line length 45–75 characters for prose.
- Prices use tabular numerals.

## Primitives

| Component | Notes |
|---|---|
| `Button` | variants: primary, secondary, ghost, danger; loading state |
| `Input` / `Textarea` | label, hint, error, `aria-describedby` |
| `Select` | native or accessible listbox |
| `Card` | product/meta container |
| `Badge` | stock/status |
| `Skeleton` | loading placeholders |
| `EmptyState` | icon + message + action |
| `ErrorState` | message + retry |
| `Dialog` / `Drawer` | focus trap, Esc, scroll lock |
| `QuantityStepper` | min 1, max stock |
| `Price` | `Intl.NumberFormat`, string input |
| `Toast` | success/error, `aria-live` |

## Layout

- Max content width ~1200 px.
- 12-column grid on desktop, single column on mobile.
- Sticky header with cart badge.
- Mobile-first breakpoints: 640 / 768 / 1024 / 1280.

## Accessibility baseline

- WCAG 2.2 AA contrast (4.5:1 text, 3:1 UI).
- Visible `:focus-visible` rings; never remove outlines.
- All interactive elements reachable by keyboard.
- Form fields always labelled.
- Images need alt text (when images exist).
- Respect `prefers-reduced-motion`.
- Target size ≥ 24×24 px (44×44 recommended).
- Test with keyboard + screen reader basics.

## Rules

1. New component → add to the inventory doc and a story/test.
2. No inline styles except dynamic values.
3. No color-only status indicators; pair with text/icon.
4. Prices always formatted via the shared `Price` component.
5. Loading, empty, and error are part of every component's contract.

## Related

- `../../../docs/07-components.md`
- `../../../docs/09-ux-accessibility.md`
