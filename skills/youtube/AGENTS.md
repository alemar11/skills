# YouTube Maintenance


- Normal runtime execution stays on `scripts/youtube`; the implementation is a
  standard-library Python artifact with no maintenance project.
- `VERSION` in `scripts/youtube` is the CLI semver source of truth. Use major
  for breaking command or JSON changes, minor for compatible capabilities, and
  patch for compatible fixes.
- Validate shipped CLI changes with `python3 -m unittest discover -s tests`,
  `scripts/youtube --help`, `scripts/youtube --version`,
  `scripts/youtube --json doctor`, a missing-`yt-dlp` preflight fixture, and a
  safe read-only live check when YouTube is reachable.
