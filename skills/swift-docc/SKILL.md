---
name: swift-docc
description: Author, review, preview, or publish Swift-DocC symbol documentation, articles, and tutorials.
---

# Swift-DocC

Use the local summaries and bundled DocC sources for authoring guidance.
Compiler and renderer internals are outside this skill's coverage; handle a
request for those through the relevant sources rather than redirecting the
user back to authoring.

Read [source map](references/source-map.md) to select the reference for the
requested task. If the DocC concept is already clear, use the matching summary:

- Symbol comments: [symbol docs](references/symbol-docs.md).
- Catalogs and articles: [articles and structure](references/articles-and-structure.md).
- Symbol and content links: [linking](references/linking.md).
- Snippets, media, and layout: [formatting and assets](references/formatting-and-assets.md).
- Interactive tutorials: [tutorial workflow](references/tutorial-workflow.md).
- Build, preview, or hosting: [preview and publish](references/preview-and-publish.md).
- Directive syntax: [directive map](references/directive-map.md).

Open the linked source under `assets/DocCDocumentation.docc/` when exact syntax
or examples matter. Consult `assets/manifest.json` only for source provenance.
Report the relevant build result when changing a catalog; do not imply a
successful preview or publication from source edits alone.
