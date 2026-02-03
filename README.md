# Codex Skills

This directory contains reusable Codex skills—task-specific packages of instructions, resources, and optional scripts that help Codex follow workflows reliably.

## Skills
- `ask-questions-if-underspecified/` — Clarify requirements before implementing when a request is underspecified.
- `learn/` — Capture durable corrections or preferences and write them to AGENTS.md.
- `postgres/` — Connect to Postgres databases and run queries or checks.

## Install With skill-installer
Copy/paste one of these prompts:

- `Use $skill-installer to install skills from <owner>/<repo> --path skills/ask-questions-if-underspecified skills/learn skills/postgres`
- `Use $skill-installer to install skills from <owner>/<repo> --path skills/ask-questions-if-underspecified`
- `Use $skill-installer to install skills from <owner>/<repo> --path skills/learn`
- `Use $skill-installer to install skills from <owner>/<repo> --path skills/postgres`

Replace `<owner>/<repo>` with your repo location. Restart Codex to pick up new skills.

## Developer Mode
Use `bootstrap.sh` on macOS to create a symlink at `~/Developer/Skills` pointing to this repo for quick access.
