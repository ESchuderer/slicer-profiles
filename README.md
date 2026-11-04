# slicer-profiles

Generates Bambu Studio user presets for the Bambu Lab H3C from a few tables: third-party filaments on the H3C Generic parents for each nozzle, and print styles (Strong, MM-Support) on the stock print presets, so a change is made once in data and reaches every nozzle. Download the ready-made zip or generate your own.

v0.1.0 and earlier targeted the Snapmaker U1, Bambu Lab P2S and Qidi X-Max 4; those printers are no longer maintained, and their release stays available as history. OrcaSlicer returns as a target once a stable release ships H3C profiles.

## Download

The zip is attached to each [release](https://github.com/ESchuderer/slicer-profiles/releases/latest): [docs/install.md](docs/install.md). What the presets set: [docs/profiles.md](docs/profiles.md). Every preset: [docs/catalog.md](docs/catalog.md).

## Layout

| Path | What it is |
| --- | --- |
| `config/h3c.json` | The printer: nozzles, the stock print preset per nozzle, the stock Generic filament preset per material and nozzle, print styles and variants |
| `config/filaments.json` | One entry per filament: material, maker notes, the maker's values |
| `config/gcode-commands.txt` | G-code words a preset may run (none today); the lint refuses any other |
| `upstream.lock.toml` | The Bambu Studio release the presets are built for and its stock profile tree |
| `src/generate.py` | Builds the presets into `out/bambu/` |
| `src/resolve.py` | Resolves stock preset inheritance; shows the value of any stock setting |
| `src/fetch.py`, `src/targets.py` | Fetch and read the pinned stock profiles |
| `src/lint.py`, `src/install.py`, `src/release.py`, `src/docs.py` | G-code and address lint, install guard, release files, generated docs |
| `scripts/build.sh` | Generate into `out/` and install into Bambu Studio |
| `scripts/release.sh` | Build the release files into `dist/` (`--publish` creates the GitHub release) |
| `tests/` | pytest tests, `check.sh` (the generated output against the golden files in `tests/golden/`) |

## Build your own

Close Bambu Studio, then `scripts/build.sh` (or `--no-install` to only generate into `out/`). It installs into the preset folder Bambu Studio loads (`preset_folder` in its `.conf`: the logged-in account's folder, else `user/default`) and stops with a diff if a preset it installed was changed in the slicer since (`--force` overwrites). Change values here, not in the GUI.

## Setup

Linux with `python3`, `bash` and `git` (on macOS, generating, checking and releasing work; installing does not, since the preset folders differ). The generator reads Bambu Studio's stock profiles: `SLICER_PROFILES_BAMBU` if set, then the tree `src/fetch.py` pinned, then the installed app in `/opt/bambustudio-bin`. The presets are built for this release (`upstream.lock.toml`):

| Slicer | Version | Stock profiles |
|---|---|---|
| Bambu Studio | 02.09.01.70 | [`bambulab/BambuStudio` v02.09.01.70](https://github.com/bambulab/BambuStudio/tree/v02.09.01.70/resources/profiles) |

## Check

The gates CI runs (one required check, `check`) need [uv](https://docs.astral.sh/uv/), which installs the pinned tools from `uv.lock`:

```
uv sync --locked
uv run ruff check && uv run ruff format --check && uv run basedpyright && uv run pytest
uv run shellcheck scripts/*.sh tests/*.sh && uv run actionlint && uv run zizmor .github && uv run typos && uv run reuse lint
```

`uv run python src/fetch.py` fetches the stock profiles pinned in `upstream.lock.toml` (only their JSON files, checked against the locked commit, tree and index version) into `~/.cache/slicer-profiles/upstream`. `tests/check.sh` fetches them, regenerates every preset and compares it with the readable golden files in `tests/golden/`; CI runs it, so no slicer has to be installed. After an intended change, run `tests/check.sh --update` and review `git diff tests/golden`.

## License

| What | License |
|---|---|
| Code (`src/`, `scripts/`, `tests/`, workflows) | ISC, see [LICENSE](LICENSE) |
| Data, docs and the generated presets in the release zip | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |

`REUSE.toml` states the license of every file. Values taken from makers' data sheets and the slicers' stock profiles are cited, not relicensed. v0.1.0 and earlier releases stay MIT. The generated presets are not committed; they are published as release zips.
