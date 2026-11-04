# slicer-profiles

Generates print, filament and printer presets for OrcaSlicer, Bambu Studio, QIDI Studio and Snapmaker Orca from one set of tables, so a P2S, a Snapmaker U1 and a QIDI X-Max 4 get matching settings in every slicer that supports them. Download the ready-made zips or generate your own.

## Download

Zips per slicer are attached to each [release](https://github.com/ESchuderer/slicer-profiles/releases/latest). Unzip into the slicer's preset folder: [docs/install.md](docs/install.md). What the presets set: [docs/profiles.md](docs/profiles.md).

## Layout

| Path | What it is |
| --- | --- |
| `config/filaments.json` | One entry per filament: Orca parent, notes, overrides, Bambu Studio and QIDI Studio parents |
| `config/printers.example.json` | Template for `config/printers.json` (git-ignored): the network address, parent preset and nozzles of the U1 and the X-Max 4 |
| `src/gen_process.py` | Print-profile tables (styles per nozzle, widths, speeds, MM-Support, Decor) |
| `src/gen_filament.py` | Builds Orca filament presets from `config/filaments.json` |
| `src/gen_machine.py` | Builds the Orca "(LAN)" printer presets: those addresses plus printer fixes (bed by first filament, U1 0.6/0.8 tool-change G-code, U1 purifier and retraction, Max 4 chamber and exhaust) |
| `src/gen_bambu.py` | Ports presets to Bambu Studio-family apps: P2S to Bambu Studio, Max 4 to QIDI Studio |
| `src/gen_snapmaker.py` | Ports the U1 presets to Snapmaker Orca (fork parents, "(LAN)" printers) |
| `src/resolve.py` | Shows the resolved value of any stock preset setting; extracts the AppImages' stock profiles to `~/.cache/slicer-profile/` |
| `src/flat.py` | Flattens a preset for the slicers' command-line mode (used by the tests) |
| `scripts/build.sh` | Generate into `out/` and install into all four slicers |
| `scripts/release.sh` | Build the release zips into `dist/` (`--publish` creates the GitHub release) |
| `tests/` | `check.sh` (checksums of the generated output), `slice.sh` (command-line smoke slices), test models |
| `docs/install.md` | Import instructions for the release zips |
| `docs/profiles.md` | What the presets contain and which printer fixes the "(LAN)" presets carry |
| `.installed/` | What `build.sh` installed last and where (`#dest=`); only these files are ever replaced (git-ignored) |

## Build your own

Close all four slicers, then:

```
scripts/build.sh            # or --no-install to only generate into out/
tests/slice.sh              # optional; --all slices every preset
```

`build.sh` installs into the preset folder each app currently loads (`preset_folder` in its `.conf`: the logged-in
account's folder, else `user/default`). After logging in or out of a slicer, run it again. Restart the slicers, then
select the "(LAN)" printers for the U1 and Max 4 in Orca: they carry the network address and the printer fixes.
Change their settings here, not in the GUI, because `build.sh` replaces the files it installed.

## Setup

Linux with `python3`, `bash` and the four slicers installed where the scripts expect them (`/opt/orca-slicer`, `/opt/bambustudio-bin`, `/opt/qidi-studio-appimage`, `/opt/snapmaker-orca-appimage`). The generators read the slicers' stock profiles, so the versions matter. Instead of an installed slicer, `SLICER_PROFILES_ORCA`, `SLICER_PROFILES_BAMBU`, `SLICER_PROFILES_QIDI` and `SLICER_PROFILES_SNAPMAKER` can each point at the `resources/profiles` folder of that slicer's source at the tag below. The presets are built for these releases (`upstream.lock.toml`):

| Slicer | Version | Stock profiles |
|---|---|---|
| OrcaSlicer | 2.4.2 | [`OrcaSlicer/OrcaSlicer` v2.4.2](https://github.com/OrcaSlicer/OrcaSlicer/tree/v2.4.2/resources/profiles) |
| Bambu Studio | 02.09.01.70 | [`bambulab/BambuStudio` v02.09.01.70](https://github.com/bambulab/BambuStudio/tree/v02.09.01.70/resources/profiles) |
| QIDI Studio | 02.07.02.73 | [`QIDITECH/QIDIStudio` v2.07.02.73](https://github.com/QIDITECH/QIDIStudio/tree/v2.07.02.73/resources/profiles) |
| Snapmaker Orca | 2.4.1 | [`Snapmaker/OrcaSlicer` v2.4.1](https://github.com/Snapmaker/OrcaSlicer/tree/v2.4.1/resources/profiles) |

`config/printers.json` holds your printers' network addresses and is not committed. `scripts/build.sh` creates it from `config/printers.example.json` when it is missing: edit the addresses, then run it again.

## Check

The gates CI runs (one required check, `check`) need [uv](https://docs.astral.sh/uv/), which installs the pinned tools from `uv.lock`:

```
uv sync --locked
uv run ruff check && uv run ruff format --check && uv run basedpyright && uv run pytest
uv run shellcheck scripts/*.sh tests/*.sh && uv run actionlint && uv run zizmor .github && uv run typos
```

`tests/check.sh` regenerates every preset from `config/printers.example.json` (no addresses) and compares the files' SHA-256 sums with `tests/expected.sha256`. Run `tests/check.sh --update` after an intended change to the tables or generators and commit the new sums. A mismatch on an unchanged tree usually means a different slicer version than the table above.

## License

| What | License |
|---|---|
| Code (`src/`, `scripts/`, `tests/`, workflows) | ISC, see [LICENSE](LICENSE) |
| Data, docs and the generated presets in the release zips | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| `slicer-profiles-orca-machines` zip: the six OrcaSlicer "(LAN)" printer presets, whose start G-code is copied from OrcaSlicer's stock profiles | [AGPL-3.0-only](release/LICENSE-AGPL-3.0-only.txt), as [OrcaSlicer states for its code](https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.4.2/README.md#license) |

`REUSE.toml` states the license of every file. Values taken from makers' data sheets and the slicers' stock profiles are cited, not relicensed. v0.1.0 and earlier releases stay MIT. The generated presets are not committed; they are published as release zips.
