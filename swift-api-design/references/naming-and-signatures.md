# Naming And Signatures

Source material:
- Official page: https://swift.org/documentation/api-design-guidelines/
- Source document: https://github.com/swiftlang/swift-org-website/blob/main/documentation/api-design-guidelines/index.md

Use this reference when designing names, parameters, argument labels, defaults, and overloads.

## Naming patterns by API role

### Methods and functions

- Nonmutating queries should read like noun phrases.
- Side-effecting operations should read like imperative verb phrases.
- Factory methods should begin with `make`.

Examples:
- `distance(to:)`
- `append(_:)`
- `sort()`
- `makeIterator()`

### Mutating and nonmutating pairs

If the operation is naturally a verb:
- Use the imperative verb for the mutating form.
- Use an `-ed` or `-ing` form for the nonmutating form.

Examples:
- `sort()` / `sorted()`
- `reverse()` / `reversed()`
- `stripNewlines()` / `strippingNewlines()`

If the operation is naturally a noun:
- Use the noun for the nonmutating form.
- Use `form...` for the mutating form.

Examples:
- `union(_:)` / `formUnion(_:)`

### Types, properties, variables, and constants

- These should generally read as nouns.
- Name by role, not by type.

Prefer:
- `greeting`
- `supplier`
- `ContentView`

Avoid:
- `string`
- `widgetFactory`
- `ViewType`

### Protocols

- Use nouns for protocols that describe what something is.
- Use `able`, `ible`, or `ing` for protocols that describe capabilities.

Examples:
- `Collection`
- `Equatable`
- `ProgressReporting`

## Argument labels

### First argument

Omit the first argument label when:
- the first argument cannot be usefully distinguished from its peers, or
- the first argument completes a grammatical phrase started by the base name, or
- an initializer performs a value-preserving conversion

Examples:
- `min(x, y)`
- `x.addSubview(y)`
- `Int64(someUInt32)`

Use a first argument label when:
- the first argument starts or participates in a prepositional phrase
- omitting the label would make the call ambiguous or misleading
- defaulted arguments may be omitted and therefore should stay explicitly labeled

Examples:
- `move(from:to:)`
- `remove(at:)`
- `dismiss(animated:)`
- `split(maxSplits:)`

Design test:
- Read the full call out loud.
- If dropping the label makes the meaning worse, keep the label.

### Remaining arguments

- Label all arguments after the first unless there is a strong reason not to.
- Choose labels that explain role, not just type.
- Use the label boundary to preserve fluent English at the call site.

## Parameter names

- Parameter names should make docs read naturally.
- Name by semantic role, not placeholder convenience.
- Weakly typed parameters often need more descriptive naming.

Prefer:
- `predicate`
- `subRange`
- `newElements`
- `observer`
- `keyPath`

Avoid:
- `includedInResult`
- `r`
- `with`

## Default arguments

- Prefer a single API with sensible default arguments over large method families.
- Default values reduce noise for common cases.
- Put defaulted parameters near the end of the parameter list.

Good use case:
- optional configuration that most callers do not care about

Bad use case:
- multiple defaults that hide fundamentally different behaviors

## Overloads and ambiguity

- Methods can share a base name when they mean the same thing or clearly operate in different domains.
- Rename overloads when unconstrained polymorphism could make the meaning ambiguous.
- Never overload on return type alone.

Examples:
- `contains(_:)` can be fine across related geometric shapes or collection semantics.
- `append(_:)` and `append(contentsOf:)` are better than two generic `append(_:)` overloads when `Any` or unconstrained types would blur intent.

## Conventions worth checking

- Document computed-property complexity when it is not O(1).
- Prefer `#fileID` for production-facing APIs; use `#filePath` only when full paths are intentionally useful and the API is not end-user-facing.
- Label tuple members in public return values when names improve clarity.
- Name closure parameters that appear in your public API surface.
