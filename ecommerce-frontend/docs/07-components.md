# 07 — Components

## Design principles

- Small, composable primitives.
- Accessible by default (labels, focus, roles).
- Token-driven styling (no raw hex in feature code).
- Every component defines loading, empty, and error states where relevant.
- Money rendered through one `Price` component.

## Primitives (`components/ui`)

| Component | Props (sketch) | Notes |
|---|---|---|
| `Button` | `variant`, `size`, `loading`, `asChild` | disabled while loading |
| `IconButton` | `label`, `icon` | requires `aria-label` |
| `Input` | `label`, `error`, `hint` | links error via `aria-describedby` |
| `Textarea` | same as Input | char counter |
| `Select` | `label`, `options` | accessible listbox/native |
| `Checkbox` | `label` | |
| `Card` | `as`, `padding` | |
| `Badge` | `tone` | stock/status |
| `Skeleton` | `className` | `aria-hidden` |
| `Spinner` | `label` | |
| `Dialog` | `open`, `onOpenChange` | focus trap, Esc |
| `Drawer` | `side`, `open` | cart drawer |
| `Tabs` | `items` | admin sections |
| `Toast` | `tone`, `title` | `aria-live` |
| `EmptyState` | `title`, `description`, `action` | |
| `ErrorState` | `title`, `onRetry` | |
| `Price` | `amount: Money`, `currency` | `Intl.NumberFormat` |
| `QuantityStepper` | `value`, `min`, `max`, `onChange` | disables at bounds |
| `Pagination` | `hasMore`, `onLoadMore` | "Load more" |

## Layout (`components/layout`)

| Component | Notes |
|---|---|
| `Header` | logo, nav, search, cart badge, account |
| `MobileNav` | drawer |
| `Footer` | static links |
| `Container` | max width + padding |
| `PageHeader` | title + breadcrumbs |
| `AdminShell` | sidebar + guard |

## Catalog (`components/catalog`)

| Component | Notes |
|---|---|
| `ProductCard` | name, price, stock; links to PDP; no image yet |
| `ProductGrid` | responsive grid + skeletons |
| `ProductGallery` | placeholder until images exist |
| `CategoryChips` | filter links |
| `StockBadge` | in stock / low / out |
| `ProductDetails` | PDP layout |
| `AddToCartButton` | auth-aware, stock-aware |

## Cart (`components/cart`)

| Component | Notes |
|---|---|
| `CartDrawer` | slide-over, focus trap |
| `CartLine` | name, unit price, stepper, subtotal, remove |
| `CartSummary` | server total, checkout CTA |
| `CartEmpty` | empty state |
| `CartBadge` | item count |

## Checkout (`components/checkout`)

| Component | Notes |
|---|---|
| `OrderSummary` | snapshot of cart lines |
| `PlaceOrderButton` | pending state, idempotency key |
| `OrderConfirmation` | from `POST /orders` response |
| `CheckoutNotice` | explains no payments/address in v1 |

## Search (`components/search`)

| Component | Notes |
|---|---|
| `SearchInput` | debounced, `/` shortcut |
| `SearchResults` | list + count |
| `SearchEmpty` | no matches |

## Chat (`components/chat`)

| Component | Notes |
|---|---|
| `AssistantPanel` | drawer/page |
| `MessageList` | `role="log"`, `aria-live` |
| `MessageBubble` | user/assistant, sanitized |
| `Composer` | textarea, char count, pending |
| `TypingIndicator` | |

## Admin (`components/admin`)

| Component | Notes |
|---|---|
| `ProductTable` | sortable-ready, actions |
| `ProductForm` | create/edit, validation |
| `CategoryTable` | name, slug, actions |
| `CategoryForm` | create/rename |
| `ConfirmDialog` | destructive actions |
| `AdminGuard` | role check + 403 |

## Component contract checklist

- [ ] TypeScript props, no `any`.
- [ ] Keyboard operable.
- [ ] Visible focus.
- [ ] Loading/pending state.
- [ ] Error state where data is involved.
- [ ] Empty state for lists.
- [ ] Responsive at 360 px.
- [ ] Uses tokens, not raw styles.
- [ ] Story/test added.

## Naming

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts`.
- Utilities: `camelCase.ts`.
- One component per file; co-locate tests and stories.
