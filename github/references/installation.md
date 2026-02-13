# GitHub CLI (`gh`) Installation

## Check whether `gh` is installed

```bash
command -v gh && gh --version
```

If `command -v gh` returns a path and `gh --version` prints output, the CLI is installed.

## Install GitHub CLI

Use the official installation instructions from GitHub: https://github.com/cli/cli#installation

- macOS:
  - Homebrew: `brew install gh`
  - MacPorts: `sudo port install gh`
- Windows:
  - winget: `winget install --id GitHub.cli`
  - Chocolatey: `choco install gh`
- Linux:
  - Use your distribution package manager or follow the official setup in the link above.

## Authenticate

```bash
gh auth login
gh auth status
```

Use `gh auth status` to confirm the session before running write operations.
