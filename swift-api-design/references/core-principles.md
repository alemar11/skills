# Core Principles

Source material:
- Official page: https://swift.org/documentation/api-design-guidelines/
- Source document: https://github.com/swiftlang/swift-org-website/blob/main/documentation/api-design-guidelines/index.md

This reference distills the official Swift API Design Guidelines into a practical set of decision rules for design and review work.

## 1. Optimize for clarity at the point of use

- Judge APIs from usage sites, not from declarations in isolation.
- A declaration is written once, but the usage is read repeatedly.
- Prefer the shape that makes real code easiest to read correctly.

Design habit:
- Write 2-3 realistic call sites before finalizing the API.
- Compare the alternatives in context, including chaining, conditionals, and initialization.

## 2. Prefer clarity over brevity

- Shorter is not automatically better.
- Omit words only when the remaining API is still unambiguous.
- Add words when they clarify role, semantics, or side effects.

Good instinct:
- Remove redundancy.
- Keep the words that disambiguate meaning.

## 3. Documentation is a design tool

- Every declaration should have a doc comment, especially public API.
- Writing the summary often exposes vague names, overloaded responsibilities, and hidden edge cases.
- If the behavior is difficult to describe simply, the API may need redesign.

Summary guidelines:
- Start with a short summary fragment.
- Describe what a function does and returns.
- Describe what an initializer creates.
- Describe what a subscript accesses.
- Describe what a type, property, or protocol is.

## 4. Model semantics before naming details

Choose the API shape that matches the meaning:
- Types, properties, and nonmutating values should usually read like nouns.
- Side-effecting methods should read like imperative verb phrases.
- Boolean properties and nonmutating boolean methods should read like assertions, such as `isEmpty` or `intersects(_:)`.
- Protocols that describe what something is should be nouns.
- Protocols that describe capabilities should typically end in `able`, `ible`, or `ing`.

## 5. Use established terminology

- Prefer common, established terms over obscure or invented ones.
- Use technical terms only when they capture precise meaning.
- Keep their standard meaning intact.
- Avoid surprising experts or teaching beginners the wrong vocabulary.

Abbreviations:
- Avoid non-standard abbreviations.
- Keep only abbreviations that are broadly established in Swift or the problem domain.

## 6. Respect Swift conventions

- Prefer methods and properties over free functions unless there is no clear receiver, the function is an unconstrained generic, or free-function notation is already standard in the domain.
- Use `UpperCamelCase` for types and protocols.
- Use `lowerCamelCase` for functions, methods, properties, variables, constants, and enum cases.
- Avoid overloading solely on return type.

## 7. Treat API design as evidence-driven

When recommending a change, anchor it in:
- the before/after call site
- the semantic role of the declaration
- whether labels help or hurt fluency
- whether naming matches side effects
- whether the API is easy to document
