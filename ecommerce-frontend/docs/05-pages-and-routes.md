# 05 — Pages & Routes

## Route table

| Route | Auth | Rendering | Purpose |
|---|---|---|---|
| `/` | — | SSR/ISR | Home: hero, categories, featured products |
| `/products` | — | SSR/ISR | Product listing with category filter |
| `/products/[id]` | — | SSR/ISR | Product detail |
| `/search` | — | CSR | Search results (`?q=`) |
| `/login` | guest | CSR | Login |
| `/register` | guest | CSR | Register |
| `/cart` | user | CSR | Cart page |
| `/checkout` | user | CSR | Review + place order |
| `/account` | user | CSR | Profile (`/auth/me`) |
| `/admin` | admin | CSR | Redirect to `/admin/products` |
| `/admin/products` | admin | CSR | Product table + create/edit |
| `/admin/categories` | admin | CSR | Category table + create/rename |

## Layouts

```
app/layout.tsx            providers, fonts, global styles
├── (shop)/layout.tsx     Header + Footer + CartDrawer
├── (auth)/layout.tsx     centered card layout
├── (account)/layout.tsx  account nav
└── admin/layout.tsx      admin sidebar + guard
```

## Page specs

### Home `/`
- Data: `GET /products?limit=8&offset=0`, `GET /categories?limit=100`.
- Sections: hero, category chips, featured grid, CTA to catalog.
- States: skeleton grid, empty fallback.

### PLP `/products`
- Data: `GET /products?limit=24&offset&category_id`.
- Category filter from `GET /categories`.
- "Load more" while `items.length === limit`.
- No sort (backend unsupported).
- URL state: `?category=<uuid>` (and optionally `?page=`).

### PDP `/products/[id]`
- Data: `GET /products/{id}`.
- Show name, description, price, stock, category.
- Add-to-cart (auth required).
- Out-of-stock disables the CTA.
- 404 → `not-found` page.
- No image field — use a placeholder until the backend adds one.

### Search `/search`
- URL: `?q=`.
- Debounced input, `GET /search/products?q&limit=24`.
- Show `total` and results; link to PDP.
- Empty query, no results, and error states.

### Login `/login`
- Form: email, password.
- Form-encoded POST.
- Redirect to `?next=` or `/`.
- Link to register.
- 401 → inline error; 429 → cooldown.

### Register `/register`
- Fields: full name, email, password (8–128).
- 409 → "Email already registered".
- 422 → inline field errors.
- On success, redirect to login (or auto-login).

### Cart `/cart`
- Auth required.
- List lines with quantity stepper, remove, subtotal.
- Order summary with server `total`.
- CTA to checkout.
- Empty state.

### Checkout `/checkout`
- Auth required; empty cart redirects to `/cart`.
- Summary from cart.
- Generate/reuse idempotency key.
- Place order → confirmation.
- No payment/address fields in v1 (backend lacks them); show a note.
- Confirmation is in-memory; refreshing loses it.

### Account `/account`
- `GET /auth/me`.
- Show name, email, role.
- Logout button (client-side).
- No order history (backend gap).

### Admin `/admin/products`
- Guard role.
- Table: name, price, stock, category.
- Create/edit form (all fields).
- Delete with confirm; handle 500/409.
- Note: search index lags after edits.

### Admin `/admin/categories`
- Guard role.
- Table: name, slug.
- Create (name only), rename.
- Delete; 409 if products reference it.
- Slug does not change on rename — show a warning.

## Navigation

- Header: logo, Home, Products, Search, Cart badge, Account/Login.
- Admin link visible only to admins.
- Mobile: hamburger + cart icon.
- Footer: static links (About, Contact, Terms).

## Not built (blocked)

| Page | Blocker |
|---|---|
| `/orders`, `/orders/[id]` | no backend endpoints |
| `/forgot-password` | no backend endpoint |
| Category detail page | `GET /categories/{id}` admin-only |
| Guest checkout | no guest cart |
| Payment step | no payment API |
