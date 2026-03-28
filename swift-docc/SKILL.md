---
name: swift-docc
description: Write, structure, review, and publish Swift-DocC documentation using curated local summaries and a bundled upstream DocC source tree.
---

# Swift-DocC

## Goal

Help with Swift-DocC authoring tasks using:
- hand-written local summary pages for fast routing
- a bundled local copy of the upstream `DocCDocumentation.docc` source tree in `assets/`
- a small manifest that tracks which upstream revision is bundled locally

Use this skill for:
- writing or reviewing symbol documentation comments
- adding supplemental articles to a documentation catalog
- linking to symbols and other content
- adding snippets, images, tables, and page structure
- building interactive tutorials and tutorial directives
- understanding authoring directives such as `@Metadata`, `@DisplayName`,
  `@Tutorials`, `@Tutorial`, `@Chapter`, `@Article`, `@Row`, and `@TabNavigator`
- customizing DocC page appearance and publishing/hosting guidance

Do not use this skill for:
- Swift-DocC compiler internals
- generated `SwiftDocC` or `DocCCommandLine` API documentation
- `swift-docc-render` internals

## Quick workflow

1. Start with [references/README.md](references/README.md).
2. Pick the summary page that matches the request:
   - [document-a-swift-package.md](references/document-a-swift-package.md)
   - [document-public-symbols.md](references/document-public-symbols.md)
   - [document-api-lifecycle-and-behavior.md](references/document-api-lifecycle-and-behavior.md)
   - [add-a-docc-catalog.md](references/add-a-docc-catalog.md)
   - [preview-and-publish.md](references/preview-and-publish.md)
   - [tutorial-workflow.md](references/tutorial-workflow.md)
   - [start-here.md](references/start-here.md)
   - [symbol-docs.md](references/symbol-docs.md)
   - [articles-and-structure.md](references/articles-and-structure.md)
   - [linking.md](references/linking.md)
   - [formatting-and-assets.md](references/formatting-and-assets.md)
   - [tutorials.md](references/tutorials.md)
   - [publishing-and-customization.md](references/publishing-and-customization.md)
   - [directive-map.md](references/directive-map.md)
3. If the user asks in task language rather than DocC terminology, use
   [source-map.md](references/source-map.md) to map the request to the right
   summary page and bundled local source file.
4. Open the exact local source file under `assets/DocCDocumentation.docc/` when
   the summary page points to it.
5. Keep answers authoring-first. If the user drifts into compiler/render
   internals, say that this skill covers authored DocC guidance and point to the
   nearest relevant authoring reference.

## References

- Read [references/README.md](references/README.md) first for scope, provenance,
  and the best entrypoints.
- Read [references/source-map.md](references/source-map.md) when the user asks
  task-oriented questions like "How do I build a tutorial?" or "How do I link to
  symbols?".
- Read the summary pages before opening local source files:
  - [references/document-a-swift-package.md](references/document-a-swift-package.md)
  - [references/document-public-symbols.md](references/document-public-symbols.md)
  - [references/document-api-lifecycle-and-behavior.md](references/document-api-lifecycle-and-behavior.md)
  - [references/add-a-docc-catalog.md](references/add-a-docc-catalog.md)
  - [references/preview-and-publish.md](references/preview-and-publish.md)
  - [references/tutorial-workflow.md](references/tutorial-workflow.md)
  - [references/start-here.md](references/start-here.md)
  - [references/symbol-docs.md](references/symbol-docs.md)
  - [references/articles-and-structure.md](references/articles-and-structure.md)
  - [references/linking.md](references/linking.md)
  - [references/formatting-and-assets.md](references/formatting-and-assets.md)
  - [references/tutorials.md](references/tutorials.md)
  - [references/publishing-and-customization.md](references/publishing-and-customization.md)
  - [references/directive-map.md](references/directive-map.md)
- Read the bundled upstream source files under `assets/DocCDocumentation.docc/`
  when you need the exact authored source behind a summary page or want to grep
  broadly across the full upstream catalog.
- Read `assets/manifest.json` only when you need to confirm which upstream
  revision is bundled or whether the local asset tree should be refreshed.
