# Document Public Symbols

Use this page for source comments on public types, methods, properties, and
protocol requirements.

## Fast Path

1. Start with [Writing symbol documentation in your source files](../assets/DocCDocumentation.docc/writing-symbol-documentation-in-your-source-files.md).
2. Use [Linking to symbols and other content](../assets/DocCDocumentation.docc/linking-to-symbols-and-other-content.md) for backticked symbol links in comments and articles.
3. If the API has Swift and Objective-C representations, check [Documenting API with different language representations](../assets/DocCDocumentation.docc/Documenting%20API%20with%20different%20language%20representations/documenting-api-with-different-language-representations.md).
4. Use [Comment](../assets/DocCDocumentation.docc/Reference%20Syntax/Shared%20Syntax/Comment.md) only when you need the lower-level shared reference syntax.
5. If the API is driven by actors, async work, retries, reconnection, or lifecycle states, continue with [document-api-lifecycle-and-behavior.md](document-api-lifecycle-and-behavior.md).

## Checklist

- Add a single-sentence summary to each important public symbol.
- Add discussion only where the API contract, usage, or tradeoffs need more context.
- Document parameters, return values, and thrown errors when they matter at the call site.
- Prefer symbol links when pointing readers to related APIs.
- For async or session-based APIs, document cancellation, ordering, retries, reconnects, and state transitions where they affect callers.
- If this grows into package-level work, continue with [document-a-swift-package.md](document-a-swift-package.md).

## Open Next

| Need | Open |
| --- | --- |
| Main symbol-comment rules | [Local source](../assets/DocCDocumentation.docc/writing-symbol-documentation-in-your-source-files.md) |
| Cross-links inside comments | [Local source](../assets/DocCDocumentation.docc/linking-to-symbols-and-other-content.md) |
| Swift vs Objective-C representations | [Local source](../assets/DocCDocumentation.docc/Documenting%20API%20with%20different%20language%20representations/documenting-api-with-different-language-representations.md) |
| Shared comment reference syntax | [Local source](../assets/DocCDocumentation.docc/Reference%20Syntax/Shared%20Syntax/Comment.md) |
| Async, actor, and state-machine APIs | [Local](document-api-lifecycle-and-behavior.md) |
