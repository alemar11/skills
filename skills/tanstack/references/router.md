# TanStack Router

Use this reference when a task involves `@tanstack/react-router`, route trees, `createFileRoute`, `createRouter`, `beforeLoad`, `loader`, `loaderDeps`, `validateSearch`, `Link`, `useNavigate`, or lazy route files.

Use this umbrella reference when the Router scope is broad, mixed, or still unclear.
Recent session evidence shows this umbrella is the common useful entrypoint;
open focused Router references only when the request is already specific enough
to benefit from a narrower contract.

## What to Optimize For

- End-to-end type safety with minimal manual annotation.
- Predictable route organization and file conventions.
- Validated search params as application state.
- Loader behavior that composes cleanly with TanStack Query.
- Explicit navigation and code-splitting choices.

## Workflow

1. Check router registration first.
   Ensure the app registers the router type once so hooks and `Link` stay fully typed.
2. Validate route boundaries.
   Confirm path params, search params, layouts, and pathless groups match the actual file structure.
3. Review loaders and dependencies.
   Each loader should have a clear cache strategy, and `loaderDeps` should reflect the inputs that really trigger refetch.
4. Tighten search params.
   Prefer `validateSearch` and typed updates over ad hoc string parsing.
5. Recheck navigation ergonomics.
   Use `from` to narrow hook types when a component is route-specific, and use lazy route files when splitting is intended.

## Macro Guides

- `router-routing-structure.md`: route tree shape, route ownership, path params, and type registration.
- `router-navigation-and-search.md`: validated search params, URL state, `Link`, and navigation ergonomics.
- `router-data-loading-and-ssr.md`: loaders, `loaderDeps`, preload behavior, cache boundaries, and Router-layer SSR.
- `router-auth-and-failures.md`: `beforeLoad`, redirects, not-found paths, and route error ownership.
- `router-plugin-and-splitting.md`: router plugin wiring, generated routes, and lazy-route code splitting.
- `README.md`: quick map from Router problem shape to the right
  macro guide or focused reference.

## Focused Reference Routing

- Stay here for mixed route-tree work, route migrations, breadcrumb/design
  questions, or implementation reviews that touch several Router features.
- Start with the matching focused Router reference when the request is plainly about
  search params, path params, navigation, loaders, auth guards, code splitting,
  not-found/error handling, type registration, SSR, or plugin wiring. Read another
  only when the evidence reveals a relevant concern it owns.
- Do not fan out across the entire Router family for ordinary app work; use the
  macro guides first and open focused references only for the narrow issue at
  hand.

## Default Rules

- Register the router type once and let inference flow through the app.
- Prefer validated search params over raw `URLSearchParams` style handling.
- Use `beforeLoad` for auth gates and route-level preconditions.
- Keep critical route config in the main route file and move heavy components to lazy files when appropriate.
- Prefer route loaders for route-owned fetching, especially when paired with TanStack Query preloading.
- Use `from` on hooks and links when narrowing improves precision and TypeScript performance.

## Focused References

- `router-routing-structure.md`: Router core model, route tree shape, path
  params, file-route alignment, type registration, and inference.
- `router-navigation-and-search.md`: validated search params, typed updates,
  `Link`, `navigate`, and route-aware hook narrowing.
- `router-data-loading-and-ssr.md`: loaders, `loaderDeps`, preload behavior,
  cache boundaries, Router SSR, and Start handoff decisions.
- `router-auth-and-failures.md`: `beforeLoad`, redirects, auth
  preconditions, not-found routes, route error boundaries, and failure
  ownership.
- `router-plugin-and-splitting.md`: generated routes, build wiring, lazy
  route files, and route-level code splitting.

## Review Checklist

- Is the router registered correctly for global type inference?
- Are search params validated and updated through typed APIs?
- Do loaders use `loaderDeps` or equivalent cache boundaries where needed?
- Are auth redirects and route guards implemented in `beforeLoad` instead of leaking into components?
- Are route files organized in a way that matches URL structure and layout ownership?

## Avoid

- Mixing React Router or Next.js assumptions into TanStack Router code.
- Manually annotating values that Router already infers.
- Leaving search params unvalidated.
- Putting server-only logic directly in client-first loaders.
- Treating lazy route files as a dumping ground for core route configuration.

## Verification

When the task depends on exact current Router APIs or filenames, compare against the installed `@tanstack/intent` Router skills if available, otherwise verify with the current TanStack Router docs.
