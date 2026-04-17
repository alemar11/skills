# Document API Lifecycle And Behavior

Use this page when the API surface is driven by async work, actors,
reconnection, retries, long-lived sessions, or explicit state transitions.

## Fast Path

1. Start with [Writing symbol documentation in your source files](../assets/DocCDocumentation.docc/writing-symbol-documentation-in-your-source-files.md).
2. Use [Linking to symbols and other content](../assets/DocCDocumentation.docc/linking-to-symbols-and-other-content.md) so states, errors, events, and related APIs point to each other.
3. If the package needs lifecycle or concurrency guidance that does not fit well in symbol comments, add an article or landing page with [Adding supplemental content to a documentation catalog](../assets/DocCDocumentation.docc/adding-supplemental-content-to-a-documentation-catalog.md).
4. If the API needs an end-to-end package workflow, continue with [document-a-swift-package.md](document-a-swift-package.md).

## Checklist

- Summarize what async work the symbol performs and what the caller should expect.
- Document thrown errors, cancellation, retries, reconnect behavior, and side effects when they matter at the call site.
- Call out state transitions, lifecycle boundaries, or delivery guarantees when the API is session-based or event-driven.
- Link related state enums, error types, event payloads, and coordination APIs instead of repeating their meaning in every symbol comment.
- If the lifecycle model is larger than one symbol can explain, move the overview into a `.docc` article and keep symbol comments focused.

## Open Next

| Need | Open |
| --- | --- |
| Main symbol-comment rules | [Local source](../assets/DocCDocumentation.docc/writing-symbol-documentation-in-your-source-files.md) |
| Cross-links between states, errors, and events | [Local source](../assets/DocCDocumentation.docc/linking-to-symbols-and-other-content.md) |
| Package-level workflow | [Local](document-a-swift-package.md) |
| Add lifecycle or architecture articles | [Local](add-a-docc-catalog.md) |
