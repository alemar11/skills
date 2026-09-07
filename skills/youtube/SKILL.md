---
name: youtube
description: Search YouTube videos and playlists or answer from timestamped transcripts. Use for YouTube links and spoken-content research.
---

# YouTube

Use `<skill-root>/scripts/youtube --json` for search and captions. Read
[CLI reference](references/cli.md) for exact options and
[states](references/states.md) when interpreting partial results or status fields.

- Topic: `videos search`, then retrieve relevant transcripts.
- Video: `transcripts get`; inspect `transcripts languages` if language matters.
- Playlist: `playlists list` for scope, then `playlists search-transcripts` for
  spoken-content search. Use `--max-videos 0` only for a requested complete scan.

Network commands already check `yt-dlp`; run `doctor` or `preflight` separately
only to diagnose availability. If access fails, report the cause and preserve
usable partial evidence. Do not silently install dependencies or use a paid
provider.

Cite timestamped moment links. Prefer manual captions and disclose automatic
captions or coverage gaps. Captions do not establish unspoken visuals; never
infer missing speech from titles or descriptions. Keep quotes brief.

Use browser cookies only when the user places account-scoped or restricted
content in scope; never export or persist cookies. Successful retrieval uses
`~/.cache/dotagents/skills/youtube/`; use `--no-cache` when requested. This skill
provides reads, not uploads or account changes.
