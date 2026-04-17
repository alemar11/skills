#!/usr/bin/env sh

set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This script is intended for macOS only." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SOURCE_DIR="$ROOT_DIR/skills"
SKILLS_DEST_DIR="$HOME/.agents/skills"
PERSONAL_MARKETPLACE_DIR="$HOME/.agents/plugins"
PERSONAL_MARKETPLACE_DEST="$PERSONAL_MARKETPLACE_DIR/marketplace.json"
PERSONAL_PLUGIN_ROOT="$PERSONAL_MARKETPLACE_DIR/plugins"
PLUGIN_MARKETPLACE_SOURCE="$ROOT_DIR/.agents/plugins/marketplace.json"
PLUGIN_TREE_SOURCE="$ROOT_DIR/plugins"
LEGACY_PLUGIN_TREE_DEST="$PERSONAL_MARKETPLACE_DIR/plugins"

mkdir -p "$SKILLS_DEST_DIR" "$PERSONAL_MARKETPLACE_DIR" "$PERSONAL_PLUGIN_ROOT"

DEPRECATED_BUNDLED_SKILLS="git-commit github github-ci github-releases github-reviews github-triage yeet"

link_path() {
  source_path="$1"
  target_path="$2"
  label="$3"

  if [ -L "$target_path" ]; then
    rm -f "$target_path"
  elif [ -e "$target_path" ]; then
    echo "SKIP $label -> $target_path already exists (not a symlink)"
    return 1
  fi

  ln -s "$source_path" "$target_path"
  echo "LINK $label -> $target_path"
}

prune_deprecated_skill_link() {
  skill_name="$1"
  target_path="$SKILLS_DEST_DIR/$skill_name"

  [ -L "$target_path" ] || return 0

  resolved_path="$(readlink "$target_path" || true)"
  case "$resolved_path" in
    "$ROOT_DIR"/*)
      rm -f "$target_path"
      echo "REMOVE deprecated bundled skill link -> $target_path"
      ;;
  esac
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to merge the personal plugin marketplace." >&2
  exit 1
fi

echo "Linking local skills and wiring plugins from: $ROOT_DIR"
echo "Skills source directory: $SKILLS_SOURCE_DIR"
echo "Skills target directory: $SKILLS_DEST_DIR"
echo "Plugin symlink root: $PERSONAL_PLUGIN_ROOT"
echo "Personal marketplace file: $PERSONAL_MARKETPLACE_DEST"
echo

for skill_name in $DEPRECATED_BUNDLED_SKILLS; do
  prune_deprecated_skill_link "$skill_name"
done

skill_count=0
skill_linked_count=0
skill_skip_count=0

for skill_dir in "$SKILLS_SOURCE_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue

  skill_name="$(basename "$skill_dir")"
  target_path="$SKILLS_DEST_DIR/$skill_name"
  skill_count=$((skill_count + 1))

  if link_path "$skill_dir" "$target_path" "$skill_name"; then
    skill_linked_count=$((skill_linked_count + 1))
  else
    skill_skip_count=$((skill_skip_count + 1))
  fi
done

plugin_linked_count=0
plugin_skip_count=0

echo
echo "Plugin wiring:"

legacy_marketplace_input=""
if [ -L "$PERSONAL_MARKETPLACE_DEST" ]; then
  legacy_marketplace_input="$(mktemp)"
  cp "$PERSONAL_MARKETPLACE_DEST" "$legacy_marketplace_input"
  rm -f "$PERSONAL_MARKETPLACE_DEST"
  echo "MIGRATE marketplace.json symlink -> regular file"
fi

if [ -L "$LEGACY_PLUGIN_TREE_DEST" ] && [ "$(readlink "$LEGACY_PLUGIN_TREE_DEST")" = "$PLUGIN_TREE_SOURCE" ]; then
  rm -f "$LEGACY_PLUGIN_TREE_DEST"
  echo "REMOVE legacy plugin tree symlink -> $LEGACY_PLUGIN_TREE_DEST"
fi

if [ -f "$PLUGIN_MARKETPLACE_SOURCE" ] && [ -d "$PLUGIN_TREE_SOURCE" ]; then
  if PLUGIN_MARKETPLACE_SOURCE="$PLUGIN_MARKETPLACE_SOURCE" \
    PERSONAL_MARKETPLACE_DEST="$PERSONAL_MARKETPLACE_DEST" \
    PERSONAL_PLUGIN_ROOT="$PERSONAL_PLUGIN_ROOT" \
    ROOT_DIR="$ROOT_DIR" \
    LEGACY_MARKETPLACE_INPUT="$legacy_marketplace_input" \
    python3 <<'PY'
import json
import os
from pathlib import Path


def load_json(path_str):
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def remove_path(path):
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    for child in path.iterdir():
        remove_path(child)
    path.rmdir()


source_marketplace_path = Path(os.environ["PLUGIN_MARKETPLACE_SOURCE"])
personal_marketplace_path = Path(os.environ["PERSONAL_MARKETPLACE_DEST"])
personal_plugin_root = Path(os.environ["PERSONAL_PLUGIN_ROOT"])
repo_root = Path(os.environ["ROOT_DIR"])
legacy_marketplace_input = os.environ.get("LEGACY_MARKETPLACE_INPUT", "")

source_marketplace = load_json(str(source_marketplace_path))
if not source_marketplace:
    raise SystemExit("Source marketplace.json is missing or invalid.")

existing_marketplace = load_json(legacy_marketplace_input) or load_json(
    str(personal_marketplace_path)
)

source_name = source_marketplace.get("name") or repo_root.name
source_display_name = (
    source_marketplace.get("interface", {}).get("displayName") or source_name
)
managed_prefix = "./plugins/"
legacy_managed_prefix = f"./.codex/plugins/{source_name}/"
legacy_namespaced_prefix = f"./plugins/{source_name}/"
legacy_namespaced_root = personal_plugin_root / source_name
personal_plugin_root.mkdir(parents=True, exist_ok=True)

if existing_marketplace:
    merged_marketplace = existing_marketplace
else:
    merged_marketplace = {
        "name": "personal",
        "interface": {"displayName": source_display_name},
        "plugins": [],
    }

existing_plugins = merged_marketplace.get("plugins")
if not isinstance(existing_plugins, list):
    existing_plugins = []

source_plugins = source_marketplace.get("plugins")
if not isinstance(source_plugins, list):
    raise SystemExit("Source marketplace plugins must be a list.")

managed_plugins = []
for plugin in source_plugins:
    plugin_name = plugin.get("name")
    if not plugin_name:
        raise SystemExit("Each source marketplace plugin requires a name.")

    source_info = plugin.get("source", {})
    if source_info.get("source") != "local":
        raise SystemExit(f"Plugin {plugin_name} must use a local source.")

    source_path = source_info.get("path")
    if not source_path:
        raise SystemExit(f"Plugin {plugin_name} is missing source.path.")

    source_dir = (
        Path(source_path)
        if os.path.isabs(source_path)
        else (repo_root / source_path).resolve()
    )
    if not source_dir.is_dir():
        raise SystemExit(f"Plugin source directory not found: {source_dir}")

    target_dir = personal_plugin_root / plugin_name
    remove_path(target_dir)
    target_dir.symlink_to(source_dir, target_is_directory=True)

    managed_plugin = dict(plugin)
    managed_plugin["source"] = {
        "source": "local",
        "path": f"{managed_prefix}{plugin_name}",
    }
    managed_plugins.append(managed_plugin)

if legacy_namespaced_root.exists() or legacy_namespaced_root.is_symlink():
    remove_path(legacy_namespaced_root)

managed_by_name = {plugin["name"]: plugin for plugin in managed_plugins}
merged_plugins = []
seen_names = set()

for plugin in existing_plugins:
    plugin_name = plugin.get("name")
    plugin_path = plugin.get("source", {}).get("path", "")
    if plugin_name in managed_by_name:
        merged_plugins.append(managed_by_name[plugin_name])
        seen_names.add(plugin_name)
        continue
    if isinstance(plugin_path, str) and (
        plugin_path.startswith(managed_prefix)
        or plugin_path.startswith(legacy_namespaced_prefix)
        or plugin_path.startswith(legacy_managed_prefix)
    ):
        continue
    merged_plugins.append(plugin)

for plugin in managed_plugins:
    if plugin["name"] not in seen_names:
        merged_plugins.append(plugin)

merged_marketplace["plugins"] = merged_plugins
merged_marketplace.setdefault("interface", {})
merged_marketplace["interface"].setdefault("displayName", source_display_name)
if merged_marketplace.get("name") in ("", None, source_name):
    merged_marketplace["name"] = "personal"
else:
    merged_marketplace.setdefault("name", "personal")

personal_marketplace_path.parent.mkdir(parents=True, exist_ok=True)
tmp_output = personal_marketplace_path.with_suffix(".tmp")
with tmp_output.open("w", encoding="utf-8") as handle:
    json.dump(merged_marketplace, handle, indent=2)
    handle.write("\n")
tmp_output.replace(personal_marketplace_path)

print(f"INSTALL marketplace namespace -> {source_name}")
print(f"INSTALL plugin symlinks refreshed -> {len(managed_plugins)}")
print(f"INSTALL marketplace entries merged -> {len(managed_plugins)}")
PY
  then
    plugin_linked_count=$((plugin_linked_count + 1))
  else
    plugin_skip_count=$((plugin_skip_count + 1))
  fi
else
  plugin_skip_count=$((plugin_skip_count + 1))
fi

if [ -n "$legacy_marketplace_input" ]; then
  rm -f "$legacy_marketplace_input"
fi

echo
echo "Completed."
echo "Skills processed: $skill_count, linked: $skill_linked_count, skipped: $skill_skip_count"
echo "Plugin wiring steps completed: $plugin_linked_count, skipped: $plugin_skip_count"
