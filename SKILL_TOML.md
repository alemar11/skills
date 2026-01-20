# SKILL.toml Plan

## Research Findings
- Codex skills are defined by a required `SKILL.md` with YAML frontmatter (`name`, `description`) plus optional resources (`scripts/`, `references/`, `assets/`). Skills can live in repo-scoped or user-scoped locations and are loaded at startup. citeturn0search1turn0search2
- The Codex team merged PR #9125 on Jan 15, 2026 to add support for an optional `SKILL.toml` file that holds **skill metadata** for a richer UI experience. citeturn2view0
- `SKILL.toml` centers on an `[interface]` block with optional fields such as `display_name`, `short_description`, `icon_small`, `icon_large`, `brand_color`, and `default_prompt`. The PR notes that these fields are exposed via the app-server API, and `display_name` + `short_description` are consumed by the TUI. citeturn2view0turn6view0
- The protocol now treats `short_description` from `SKILL.md` as legacy and prefers `SKILL.toml`’s `interface.short_description`. `brand_color` and `default_prompt` were added to the interface model in a follow-up commit. citeturn4view0turn6view0
- Icon paths must be **relative paths under the skill’s `assets/` directory**; paths outside `assets/` (including absolute paths) are ignored. citeturn5view0
- Codex supports symlinked **skill folders**. The PR notes deprecating symlinks to `SKILL.md` files directly, so prefer directory symlinks only. citeturn1search4turn5view0

## Implementation Plan
1. **Decide scope**: Add a `SKILL.toml` per skill folder where UI metadata is useful (start with the most visible skills).
2. **Define interface metadata**: For each skill, choose `display_name` and `short_description` that are user-facing (distinct from the trigger-oriented `description` in `SKILL.md`).
3. **Add assets**: If using icons, place them under `assets/` and reference them with relative paths in `SKILL.toml`.
4. **Keep `SKILL.md` intact**: Preserve `name` and `description` for skill triggering; treat `SKILL.toml` as additive metadata.
5. **Validate behavior**: Restart Codex and confirm the skill list/UI shows the `display_name` and `short_description`. If not, confirm the Codex version includes PR #9125 and that paths are correct.
6. **Document the new convention**: Update repository docs to state that `SKILL.toml` is optional metadata per skill, and that icons must live in `assets/`.
7. **Avoid deprecated patterns**: Use symlinked skill directories if needed, but do not symlink `SKILL.md` files directly.
