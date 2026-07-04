# Frontend Developer Guide

`AGENTS.md` is a symlink to this file — edit only `CLAUDE.md`.

## Design system

**Tailwind v4 + shadcn/ui.** All UI uses components from `src/components/ui/` (shadcn copy-ins). No other UI component libraries.

### Semantic token discipline

Never use raw Tailwind palette classes. Always use semantic tokens:

| Wrong | Right |
|---|---|
| `bg-gray-100` | `bg-muted` |
| `text-gray-500` | `text-muted-foreground` |
| `border-gray-200` | `border-border` |
| `bg-red-500` | `bg-destructive` |
| `text-blue-600` | `text-primary` |

Tokens are defined in `src/index.css` under `:root`/`.dark` and mapped to Tailwind utilities via the `@theme inline` block. Adding a named theme or per-campaign theme later requires only new CSS variable sets — zero component changes — only if this rule is maintained.

### `cn()` for conditional classes

```ts
import { cn } from "@/lib/utils";
className={cn("base-class", isActive && "active-class")}
```

## Components

### shadcn only

Never add new npm UI component libraries. If you need a UI element not yet in `src/components/ui/`, add it with:

```bash
npx shadcn@latest add <component>
```

### Icons

`lucide-react` only. Never install other icon libraries.

### Component hierarchy

Route files (`src/routes/`) are routing config only: `beforeLoad`, `loader`, `validateSearch`, `errorComponent`, `pendingComponent`, and a `component` pointing at a page. They render no JSX of their own.

Every route's `component` (and `pendingComponent`/`errorComponent`, when present) is a page component that lives in `src/pages/`, one file per route. A page needs its route's params/search/loader data, so it reads them via `getRouteApi(path)` — pass the exact path string given to `createFileRoute` — instead of importing `Route` from the route file:

```tsx
// src/pages/campaign-detail-page.tsx
import { getRouteApi } from "@tanstack/react-router";

const Route = getRouteApi("/campaigns/$slug/");

export function CampaignDetailPage() {
  const { slug } = Route.useParams();
  // ...
}
```

```tsx
// src/routes/campaigns.$slug.index.tsx
import { createFileRoute } from "@tanstack/react-router";
import { CampaignDetailPage } from "@/pages/campaign-detail-page";

export const Route = createFileRoute("/campaigns/$slug/")({
  component: CampaignDetailPage,
});
```

Layout routes (routes rendering `<Outlet />`, e.g. `__root.tsx`, `campaigns.$slug.tsx`) follow the same rule, but their component lives in `src/layouts/` instead of `src/pages/`, since they wrap children rather than render a leaf page.

Extract a feature component (`src/components/`) out of a page when:
- The page's JSX grows complex or mixes data, state, and markup in one place
- The same UI is reused across pages
- The component owns internal state or mutations

Feature components own a single concern: markup, internal UI state, and mutations.

## Forms

Every form uses shadcn `Form` + `react-hook-form` + Zod + `@hookform/resolvers`:

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
```

Never manage form field values with plain `useState`.

## Dialogs over inline forms

All create/edit/delete flows open a `Dialog`, or redirect to a dedicated page. Never use `window.confirm`. Never expand forms inline within a page.
