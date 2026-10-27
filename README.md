# slicer-profiles

Generates print, filament and printer presets for OrcaSlicer, Bambu Studio, QIDI Studio and Snapmaker Orca from one set of tables, so a P2S, a Snapmaker U1 and a QIDI X-Max 4 get matching settings in every slicer that supports them.

| File | What it is |
| --- | --- |
| `filaments.json` | One entry per filament: Orca parent, notes, overrides, Bambu Studio and QIDI Studio parents |
| `gen_process.py` | Print-profile tables (styles per nozzle, widths, speeds, MM-Support, Decor) |
| `gen_filament.py` | Builds Orca filament presets from `filaments.json` |
| `printers.example.json` | Template for `printers.json` (git-ignored): the network address, parent preset and nozzles of the U1 and the X-Max 4 |
| `gen_machine.py` | Builds the Orca "(LAN)" printer presets: those addresses plus printer fixes (bed by first filament, U1 0.6/0.8 tool-change G-code, U1 purifier and retraction, Max 4 chamber and exhaust) |
| `gen_bambu.py` | Ports presets to Bambu Studio-family apps: P2S to Bambu Studio, Max 4 to QIDI Studio |
| `gen_snapmaker.py` | Ports the U1 presets to Snapmaker Orca (fork parents, "(LAN)" printers) |
| `resolve.py` | Shows the resolved value of any stock preset setting; extracts the AppImages' stock profiles to `~/.cache/slicer-profile/` |
| `flat.py` | Flattens a preset for the slicers' command-line mode (used by the tests) |
| `build.sh` | Generate into `out/` and install into all four slicers |
| `test_slice.sh` | Smoke-test slices from the command line (`--all` for every preset) |
| `installed-*.txt` | What `build.sh` installed last and where (`#dest=`); only these files are ever replaced |

`build.sh` installs into the preset folder each app currently loads (`preset_folder` in its `.conf`: the logged-in
account's folder, else `user/default`). After logging in or out of a slicer, run `./build.sh` again.

Typical run (close all four slicers first):

```
./build.sh            # or ./build.sh --no-install to only generate
./test_slice.sh       # optional; --all slices every preset
```

Then restart the slicers. In Orca, select the "(LAN)" printers for the U1 and Max 4:
they carry the network address and the printer fixes. Change their settings here, not in the GUI,
because `build.sh` replaces the files it installed.

## Setup

Linux with `python3`, `bash` and the four slicers installed where the scripts expect them (`/opt/orca-slicer`, `/opt/bambustudio-bin`, `/opt/qidi-studio-appimage`, `/opt/snapmaker-orca-appimage`). The generators read the slicers' stock profiles, so the versions matter. Output was verified with:

| Slicer | Version | Arch Linux package |
|---|---|---|
| OrcaSlicer | 2.4.2 | `orca-slicer-bin` 2.4.2-3 |
| Bambu Studio | 02.08.02.61 | `bambustudio-bin` 02.08.02.61-1 |
| QIDI Studio | 2.07.02.73 | `qidi-studio-appimage` 2.07.02.73-1 |
| Snapmaker Orca | 2.4.0 | `snapmaker-orca-appimage` 2.4.0-1 |

`printers.json` holds your printers' network addresses and is not committed. `build.sh` creates it from `printers.example.json` when it is missing: edit the addresses, then run it again.

## Check

`./check.sh` regenerates every preset with the example addresses and compares the files' SHA-256 sums with `expected.sha256`. Run `./check.sh --update` after an intended change to the tables or generators and commit the new sums. A mismatch on an unchanged tree usually means a different slicer version than the table above.

## License

MIT, see [LICENSE](LICENSE). The generated presets inherit from each slicer's stock profiles and are not part of this repository.
