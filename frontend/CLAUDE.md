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

Route files are orchestrators — they read from the query cache and compose feature components. They do not import from `@/components/ui/` directly.

Feature components (in `src/components/`) own a single concern: markup, internal UI state, and mutations. shadcn primitives live inside feature components.

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

All create/edit/delete flows open a `Dialog`. Never use `window.confirm`. Never expand forms inline within a page.
