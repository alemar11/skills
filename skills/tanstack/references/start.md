# TanStack Start

Use this reference when a task involves `@tanstack/react-start`, `createServerFn`, middleware, server routes, SSR, hydration, environment variables, cookies, or auth flows in a TanStack Start app.

Use this umbrella reference when the Start scope spans multiple framework concerns
or when the exact subdomain is still unclear. For targeted work, read the
matching focused reference instead of solving every Start concern from one broad
prompt.
Recent session evidence favors this umbrella for real Start app work; use the
focused Start references only when the request has already narrowed to one
Start subdomain.

## What to Optimize For

- Correct server/client boundaries.
- Safe handling of secrets and environment variables.
- Current server-function APIs and middleware order.
- SSR and hydration behavior that matches TanStack Start's execution model.
- Clear separation between route code, server-only logic, and shared types.

## Workflow

1. Establish the execution model first.
   TanStack Start is isomorphic by default; check where code actually runs before changing loaders, imports, or env access.
2. Move server-only work to server functions.
   Database access, filesystem access, and secrets should live behind `createServerFn(...)` or other server-only boundaries.
3. Validate inputs at the boundary.
   Prefer the current server-function validation API used by the installed TanStack version.
4. Review middleware and auth flow.
   Keep request shaping, auth checks, and shared server concerns in middleware or server utilities rather than scattered component logic.
5. Recheck SSR and hydration safety.
   Watch for browser-only APIs, module-level env leaks, and server/client mismatch patterns.

## Macro Guides

- `start-framework-and-execution.md`: framework setup, isomorphic boundaries, and deciding where code should live.
- `start-server-functions-and-routes.md`: `createServerFn`, validation, server helpers, and server routes.
- `start-middlewares-and-server-core.md`: middleware ownership, shared request concerns, and server-runtime boundaries.
- `start-server-components-and-migrations.md`: experimental server components and Next.js App Router migrations.
- `start-deployments.md`: deployment targets, packaging assumptions, and runtime-sensitive tradeoffs.
- `README.md`: quick map from Start problem shape to the right macro
  guide or focused reference.

## Focused Reference Routing

- Stay here for mixed Start app reviews, server/client boundary audits, or
  framework-level implementation changes that touch several concerns.
- Start with the matching focused Start reference for isolated server-function,
  middleware, execution-model, server-route, deployment, migration, or
  experimental server-component work. Read another only when the evidence reveals
  a relevant concern it owns.
- Do not open every Start focused reference during normal implementation; open the
  umbrella reference map first, then use focused guidance only when it will
  reduce ambiguity.

## Default Rules

- Treat loaders as isomorphic unless the current framework docs prove otherwise.
- Keep secrets out of shared modules and client bundles.
- Prefer `VITE_` public environment variables for client-visible config in Vite-based Start apps.
- Verify the current server-function validator API for the installed version instead of copying stale examples.
- Keep server-only files and shared files clearly separated.
- Use middleware for reusable request concerns rather than repeating auth and header logic.

## Focused References

- `start-framework-and-execution.md`: React Start app setup, Start core
  runtime patterns, isomorphic boundaries, shared-module safety, and runtime
  placement.
- `start-server-functions-and-routes.md`: `createServerFn`, validation,
  server-only helpers, raw HTTP handling, and API-style server routes.
- `start-middlewares-and-server-core.md`: middleware ordering, auth,
  cookies, headers, reusable request concerns, server runtime behavior, and
  server-only module boundaries.
- `start-server-components-and-migrations.md`: experimental server
  components, composition caveats, caching caveats, and Next.js App Router
  migration work.
- `start-deployments.md`: deployment targets, runtime packaging,
  environment-sensitive behavior, and target-specific constraints.

## Review Checklist

- Is any server-only work happening directly in loaders or shared modules?
- Are secrets or raw `process.env` values leaking into code that can ship client-side?
- Are server-function inputs validated using the current supported API?
- Does middleware own shared auth, session, or header concerns where appropriate?
- Are SSR and hydration edge cases handled for browser-only code?

## Avoid

- Assuming TanStack Start behaves like Next.js or Remix.
- Using outdated community examples without checking the installed version.
- Using `NEXT_PUBLIC_` naming in a Vite-based Start setup.
- Leaving server-function input validation implicit.
- Hiding server/client boundary problems behind type casts.

## Verification

When exact Start APIs matter, compare against the installed `@tanstack/intent` Start skills if available, otherwise verify with the current TanStack Start docs before finalizing guidance.
