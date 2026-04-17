# Swift-DocC References

Curated local references for the `swift-docc` skill.

## How To Use This Set

- Start with a hand-written summary page.
- Open the exact local source file inside `../assets/DocCDocumentation.docc/`
  when the summary points to one.

## Best Entry Points

- [document-a-swift-package.md](document-a-swift-package.md): fastest path for documenting a package or library API end to end.
- [document-public-symbols.md](document-public-symbols.md): fastest path for source comments on public APIs.
- [document-api-lifecycle-and-behavior.md](document-api-lifecycle-and-behavior.md): fastest path for actors, async work, retries, sessions, and state-machine APIs.
- [add-a-docc-catalog.md](add-a-docc-catalog.md): fastest path for landing pages, articles, and topic groups.
- [preview-and-publish.md](preview-and-publish.md): fastest path for local preview, archive generation, and hosting docs.
- [tutorial-workflow.md](tutorial-workflow.md): fastest path for adding tutorials to an existing package.
- [start-here.md](start-here.md): end-to-end DocC onboarding and first reads.
- [symbol-docs.md](symbol-docs.md): symbol comments, language representations, and doc comment syntax.
- [articles-and-structure.md](articles-and-structure.md): catalogs, articles, extensions, and page structure.
- [linking.md](linking.md): symbol links, article links, tutorial links, and ambiguous references.
- [formatting-and-assets.md](formatting-and-assets.md): formatting, tables, images, layout, and page presentation.
- [tutorials.md](tutorials.md): interactive tutorial workflow, structure, media, and assessments.
- [publishing-and-customization.md](publishing-and-customization.md): previewing, publishing, and appearance customization.
- [directive-map.md](directive-map.md): directive-focused routing for API pages and tutorials.
- [source-map.md](source-map.md): generated task-to-topic map with local source links.

## Layout

- `../assets/DocCDocumentation.docc/`: bundled upstream authored source tree from `swiftlang/swift-docc`.
- `catalog.json`: source of truth for topics, local source paths, and task routing.
- `source-map.md`: generated from the catalog.
- `../assets/manifest.json`: generated stale-check and provenance metadata for the bundled source tree.

## Scope

- In scope: DocC authoring workflows, symbol docs, articles, links, formatting, tutorials, publishing, and directive routing.
- Out of scope: `SwiftDocC` API docs, `DocCCommandLine` API docs, compiler internals, and `swift-docc-render` internals.
