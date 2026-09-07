# Preview And Publish

Use this page for the last mile: previewing docs locally, building archives,
and hosting or distributing the generated output.

## Fast Path

For symbol documentation, establish current compilation and symbol graphs through
the documentation build or a relevant package build. Reuse valid evidence;
repeat compilation checks only for changed inputs or failure diagnosis. Run
tests when changed behavior or repository rules require them. Hosting an
existing archive needs no new package build.

1. Start with [Documenting a Swift framework or package](../assets/DocCDocumentation.docc/documenting-a-swift-framework-or-package.md) for the package-level preview model and [Distributing documentation to other developers](../assets/DocCDocumentation.docc/distributing-documentation-to-other-developers.md) for archive generation and hosting.
2. If the Swift-DocC plugin commands are available in the package, prefer `swift package preview-documentation` for a local render loop and `swift package generate-documentation` for an archive build.
3. If the plugin commands are unavailable but `xcrun docc` exists, use the fallback command path below after you have a `.docc` catalog.
4. If the published docs need custom branding or site styling, follow [Customizing the appearance of your documentation pages](../assets/DocCDocumentation.docc/customizing-the-appearance-of-your-documentation-pages.md).
5. If you still need to author the catalog or landing page before publishing, go back to [add-a-docc-catalog.md](add-a-docc-catalog.md).

## Local Preview Checklist

- If the package does not have a `.docc` catalog yet, add one first with [add-a-docc-catalog.md](add-a-docc-catalog.md).
- If plugin subcommands exist in the current toolchain, use them from the package root.
- If plugin subcommands are missing, fall back to `swift build` plus `xcrun docc`.

## Fallback CLI Flow

Use this flow when you need a local preview path and your toolchain does not
expose the Swift-DocC plugin subcommands:

```sh
swift build

xcrun docc preview Sources/<TargetName>/<TargetName>.docc \
  --additional-symbol-graph-dir .build \
  --fallback-display-name <TargetName> \
  --fallback-bundle-identifier com.example.<TargetName>

xcrun docc convert Sources/<TargetName>/<TargetName>.docc \
  --additional-symbol-graph-dir .build \
  --fallback-display-name <TargetName> \
  --fallback-bundle-identifier com.example.<TargetName> \
  --output-dir .build/<TargetName>.doccarchive
```

Use source-service and hosting flags from the bundled distribution guide when
you need repository links, static hosting, or a custom base path.

## Open Next

| Need | Open |
| --- | --- |
| Package-level preview and build flow | [Local source](../assets/DocCDocumentation.docc/documenting-a-swift-framework-or-package.md) |
| Archive generation and hosting | [Local source](../assets/DocCDocumentation.docc/distributing-documentation-to-other-developers.md) |
| Theme, fonts, colors, and icons | [Local source](../assets/DocCDocumentation.docc/customizing-the-appearance-of-your-documentation-pages.md) |
| Add a minimal catalog before previewing | [Local](add-a-docc-catalog.md) |
