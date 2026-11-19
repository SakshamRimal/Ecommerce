# 09 — UX & Accessibility

## Universal states

Every data-driven screen must handle:

| State | UI |
|---|---|
| Loading | skeleton/spinner, layout-stable |
| Empty | message + primary action |
| Error | message + retry |
| Unauthorized | login prompt / 403 page |
| Success | content |

No screen should render a blank page on error.

## Responsive

- Mobile-first; breakpoints 640 / 768 / 1024 / 1280.
- Header collapses to a menu + cart icon.
- Product grid: 1 / 2 / 3 / 4 columns.
- Tap targets ≥ 44×44 px.
- No horizontal scroll at 360 px.
- Sticky CTA on mobile PDP/checkout.

## Accessibility (WCAG 2.2 AA)

### Structure
- One `<h1>` per page; sequential headings.
- Landmarks: `header`, `nav`, `main`, `footer`.
- Skip-to-content link.

### Keyboard
- All controls reachable in logical order.
- Visible `:focus-visible`.
- Dialogs/drawers trap focus and restore it on close.
- `Esc` closes overlays.
- No keyboard traps.

### Forms
- Every input has a `<label>`.
- Errors linked with `aria-describedby` and `aria-invalid`.
- Required fields marked in text, not color only.
- Password fields support paste and show/hide.

### Images & icons
- Meaningful images need alt text (when images exist).
- Decorative images `alt=""`.
- Icon-only buttons need `aria-label`.

### Color & motion
- Contrast ≥ 4.5:1 text / 3:1 UI.
- Status uses text + icon, not color alone.
- Respect `prefers-reduced-motion`.
- No auto-playing carousels.

### Live regions
- Cart updates: polite announcement of item count.
- Search results: announce count.
- Chat: `role="log"` + `aria-live="polite"`.
- Toasts: `aria-live="polite"`/`assertive` for errors.

## Content & copy

- Prices formatted with currency (`Intl.NumberFormat`).
- Stock: "In stock", "Only N left", "Out of stock".
- Dates (when added): locale-aware.
- Errors: plain language, actionable.
- Buttons: verbs ("Add to cart", "Place order"), not "Submit".

## Performance UX

- Optimistic-feeling navigation via prefetch.
- Skeletons match final layout to avoid CLS.
- Images (future) with width/height, lazy below the fold.
- Debounced search; cancel stale requests.
- Keep the initial JS bundle small; lazy-load chat and admin.

## Trust & clarity

- Show that checkout does not take payment yet (v1).
- Explain that orders cannot be viewed later (until the backend adds it).
- Show a privacy note near chat (messages go to OpenAI).
- Never show raw backend errors.

## Manual QA checklist

- [ ] Keyboard-only pass on home → PDP → cart → checkout.
- [ ] Screen reader pass on login, PDP, cart.
- [ ] 360 px, 768 px, 1280 px layouts.
- [ ] Slow 3G loading states.
- [ ] Offline/network error.
- [ ] Empty search, empty cart, empty category.
- [ ] 401, 403, 404, 409, 422, 429, 500 states.
- [ ] Reduced motion.
- [ ] Zoom 200%.

## Automated checks

- `eslint-plugin-jsx-a11y`
- `axe-core` in component tests
- Lighthouse CI accessibility budget ≥ 95
- Playwright accessibility snapshot for key pages
