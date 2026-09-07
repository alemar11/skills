---
name: tanstack
description: Build, debug, review, or migrate applications using TanStack packages.
---

# TanStack

Ground recommendations in the app's installed `@tanstack/*` versions and local
framework conventions. Verify version-sensitive APIs against installed code or
current TanStack-owned documentation.

Read the product reference for the affected boundary:

- Cache, queries, mutations: [Query](references/query.md).
- Routes, search parameters, loaders: [Router](references/router.md).
- Server functions, middleware, SSR: [Start](references/start.md).
- Shared loading, prefetch, hydration: [integration](references/integration.md).
- Forms and validation: [Form](references/form.md).
- Columns and row models: [Table](references/table.md).
- Virtual lists or grids: [Virtual](references/virtual.md).
- Scaffolding and add-ons: [CLI](references/cli.md).
- Other products or narrower concerns: [reference map](references/README.md).

Load focused subreferences only for the relevant concern. Preserve application
behavior during migrations and check server/client ownership before moving
imports, code, or environment access.
