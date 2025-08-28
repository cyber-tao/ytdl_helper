

# yt-dlp Video Download Helper

ytdl_helper is a small command-line wrapper around `yt-dlp` to
download videos, subtitles and thumbnails with sensible defaults and
post-processing. The main script is `ytdl_helper.py`.

Note about environments: this README shows examples using `uv` for
dependency and environment management (the project includes
`pyproject.toml`). I assume your `uv` installation provides common
commands like `uv install` and `uv run <cmd>` to run a project-local
Python. If your `uv` variant uses different subcommands, adjust the
examples accordingly.

## Features

- Download videos/playlists and merge video+audio when necessary via ffmpeg.
- Download and embed subtitles (configurable language priority).
- Download and embed thumbnails; optional `info.json` output and cleanup.
- Support for passing a cookies file for authenticated or region-restricted
	content.
- Simple progress callback and robust retry/concurrency settings.

## Requirements

- Python >= 3.12 (per `pyproject.toml`)
- `uv` (used for environment & dependency management)
- `yt-dlp` (listed in `pyproject.toml`)
- Optional: `ffmpeg` on PATH (or provide its directory via `--ffmpeg`)

The project `pyproject.toml` declares:

- name: `ytdl_helper`
- python requirement: `>=3.12`
- dependency: `yt-dlp>=2025.6.9`

## Quick start (using uv)

Open a shell and run the following (examples assume a working `uv`):

Create / install the environment and dependencies:

```sh
# Install dependencies from pyproject.toml
uv install

# Run a single command inside the managed environment
uv run python ytdl_helper.py <url>
```

If your `uv` does not create an isolated shell, use `uv run` to execute
commands inside the environment. Replace the commands above with your
local `uv` workflow if it differs.

## Usage

Run the script with one or more URLs:

```sh
uv run python ytdl_helper.py <url1> <url2> ...
```

Common options:

- `-o, --output-dir` : output directory (default: current directory)
- `-c, --cookies` : path to cookies file (for authenticated content)
- `-l, --langs` : comma-separated subtitle language priority (default:
	`zh-Hans,zh,zh-CN,en`)
- `--ffmpeg` : directory containing ffmpeg executables if not on PATH
- `-q, --quiet` : quiet mode
- `--auto-sub` : enable automatic captions when manual subtitles are
	unavailable
- `--no-playlist` : ignore playlists and download single video only
- `--playlist-items` : select playlist items, e.g. `1-5,7,10-`
- `--write-infojson` : write `info.json` for each entry
- `--clean-infojson` : clean redundant fields in `info.json` (works with
	`--write-infojson`)

Examples:

```sh
# Download a single video to `output/`, using a cookies file and writing info.json
uv run python ytdl_helper.py "https://www.youtube.com/watch?v=CW0dn80Er4Y" -o output --cookies www.youtube.com_cookies.txt --write-infojson

# Download first 5 items of a playlist and enable automatic captions
uv run python ytdl_helper.py "https://www.youtube.com/playlist?list=..." --playlist-items 1-5 --auto-sub

# Specify local ffmpeg directory (use a path appropriate for your OS)
uv run python ytdl_helper.py <url> --ffmpeg /path/to/ffmpeg/bin
```

## Output and filenames

Files are written using the template `%(uploader)s - %(title)s.%(ext)s` by
default. Typical outputs placed into the selected output directory include:

- merged video files (e.g. `.mp4` / `.webm`)
- subtitles (`.srt`)
- thumbnails (`.jpg`)
- optional `info.json`

The repository contains an `output/` folder with example downloaded
artifacts.

## Troubleshooting

- ffmpeg errors: ensure `ffmpeg` is available on PATH or provide `--ffmpeg`.
- cookies: ensure the cookies file is in Netscape cookie format supported by
	yt-dlp and the path is correct.
- HTTP 403/429/failed downloads: try using cookies, a different network,
	or a proxy; some content may be region-restricted or require authentication.
- missing subtitles: not all videos have subtitles; `--auto-sub` may help
	when automatic captions exist.

## Project layout

- `ytdl_helper.py` — main script and CLI
- `pyproject.toml` — project metadata and dependency declaration

## Contributing

Contributions welcome. Suggested improvements: add more post-processing
options, improved error handling, or a richer CLI interface (Click/typer).

## License

No license is specified. Add a `LICENSE` file in the repo root if you want
to make the license explicit.

---

If you want, I can also:

- add an explicit `uv`-based workflow script (PowerShell) for common tasks,
- create a minimal `uv`-compatible lock/install example (if you want me to
	generate a `uv` manifest), or
- produce an English + Chinese bilingual README.


