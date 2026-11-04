# What the presets do

Every preset inherits a stock preset of the slicer by name and stores only the values set here. Everything else shows as inherited, so a slicer update that changes a stock value still reaches you. The tables live in `config/filaments.json` and in the generators in `src/`; the counts below are those of the release zips, and every preset is listed by name in [catalog.md](catalog.md). The tables on this page are generated from the same data (`src/docs.py`).

## What is in each zip

<!-- generated: zips -->

| Zip | Print presets | Filament presets | Printer presets | License |
|---|---|---|---|---|
| `orca` (OrcaSlicer) | 61: Bambu Lab P2S 20, Snapmaker U1 21, Qidi X-Max 4 20 | 9 | none | CC-BY-4.0 |
| `orca-machines` (OrcaSlicer) | none | none | 6 "(LAN)" | AGPL-3.0-only |
| `bambu` (Bambu Studio) | 20: Bambu Lab P2S 20 | 9 | none | CC-BY-4.0 |
| `qidi` (QIDI Studio) | 20: Qidi X-Max 4 20 | 9 | none | CC-BY-4.0 |
| `snapmaker` (Snapmaker Orca) | 21: Snapmaker U1 21 | 9 | 3 "(LAN)" | CC-BY-4.0 |

<!-- end generated -->

The P2S has no "(LAN)" printer preset: choose it in the slicer as usual and pick the print and filament presets. Install steps: [install.md](install.md).

## Print presets

Source: `src/gen_process.py`. Names read `<layer>mm <style> @<printer> <nozzle>`, for example `0.20mm Standard @U1 0.4`. Printer tags: `P2S`, `U1`, `X-Max4`. Each printer gets the same set for its 0.4, 0.6 and 0.8 mm nozzles, built on the stock preset for that nozzle.

<!-- generated: styles -->

| Nozzle | Style | Layer mm | Walls | Gyroid infill | Top shell mm | Bottom shell mm |
|---|---|---|---|---|---|---|
| 0.4 | Detail | 0.12 | 3 | 15 % | 1.0 | 0.8 |
| 0.4 | Quality | 0.16 | 3 | 20 % | 1.0 | 0.8 |
| 0.4 | Standard | 0.20 | 3 | 15 % | 1.0 | 0.8 |
| 0.4 | Strong | 0.20 | 5 | 40 % | 1.4 | 1.2 |
| 0.6 | Quality | 0.20 | 3 | 20 % | 1.2 | 1.0 |
| 0.6 | Standard | 0.24 | 3 | 15 % | 1.2 | 1.0 |
| 0.6 | Strong | 0.28 | 4 | 40 % | 1.6 | 1.2 |
| 0.8 | Quality | 0.28 | 2 | 20 % | 1.4 | 1.1 |
| 0.8 | Standard | 0.32 | 2 | 15 % | 1.4 | 1.1 |
| 0.8 | Strong | 0.36 | 3 | 40 % | 1.8 | 1.4 |

<!-- end generated -->

Standard is the everyday default: Quality's walls, line widths and speeds at a taller layer with lighter infill. Strong uses wider inner-wall, infill and solid-infill lines, 10 mm/s more on the outer wall and 20 mm/s more on the inner wall.

Speeds in mm/s (the filament's maximum volumetric speed still caps them). Detail prints the outer wall at 40 and the top surface at 60.

<!-- generated: speeds -->

| Nozzle | Outer wall | Inner wall | Sparse infill | Solid infill | Top surface | Gap fill | Bridge |
|---|---|---|---|---|---|---|---|
| 0.4 | 50 | 100 | 150 | 120 | 80 | 50 | 30 |
| 0.6 | 50 | 90 | 120 | 100 | 70 | 40 | 25 |
| 0.8 | 40 | 70 | 100 | 80 | 60 | 30 | 20 |

<!-- end generated -->

Set the same way in every print preset:

- Gyroid infill, Arachne walls, inner wall before outer wall, precise outer wall, aligned seam with staggered inner seams, no supports and no ironing by default.
- Arc fitting off (Orca advises it off on Klipper printers). Infill/wall overlap 15 %.
- Small-perimeter slowdown on (threshold 4 mm, 50 % speed), travel speed 400 mm/s, and one set of accelerations for all styles (outer wall 2500 in Strong, 2000 otherwise).
- Line widths scale with the nozzle (outer wall 0.42, 0.62 and 0.82 mm for the three nozzles). First-layer line width is 1.25 times the nozzle.
- Elephant-foot compensation 0.15 mm (0.2 mm on the 0.8 nozzle), because the P2S 0.6 and 0.8 stock presets have none.
- The P2S presets store one value per hotend slot in every speed and acceleration key, as many as the stock parent has: two in the OrcaSlicer zip; in the Bambu Studio zip three for the 0.4 and 0.6 nozzle presets and two for the 0.8. Every slot holds the same value. OrcaSlicer 2.4.2 reads only the first slot, so the copies have no effect there; Bambu Studio (and OrcaSlicer 2.5) read the slot of the hotend in use, so every hotend gets the same speeds.

Two variants are built on top of the styles:

- **MM-Support**: every style of every printer also exists with ` MM-Support` in the name. It prints supports with the support base in the model filament (slot 1) and the interface layers from slot or tool 2, for example PLA under PETG, with zero Z gap, and turns on the prime tower. On the U1 the tower shell uses the model filament and a wider brim, because PLA+PETG towers delaminate on Snapmaker's printer.
- **Decor** (`0.12mm Decor @U1 0.4`, U1 only): the Detail style with a scarf seam, ironed top surfaces and Snapmaker's prime-tower values for 0.12 mm layers, for multicolor display pieces.

## Filament presets

Source: `config/filaments.json`, built by `src/gen_filament.py`:

<!-- generated: filaments -->

| Material | Presets |
|---|---|
| PLA | SUNLU PLA Matte HQ, SUNLU PLA+ 2.0 HQ |
| PETG | SUNLU HS Matte PETG HQ, SUNLU PETG 2.0 HQ, eSUN PETG HQ |
| HIPS | CC3D HIPS HQ |
| ASA | Anycubic ASA HQ, SUNLU ASA HQ |
| TPU | SUNLU TPU 95A HQ |

<!-- end generated -->

Each preset inherits the stock preset of the same filament (or the generic one for the type) and sets nozzle and bed temperatures, maximum volumetric speed, density and cooling. The Notes tab of every preset carries the maker's data sheet values and drying advice. Details that matter in use:

- Bed temperature is set for the smooth, textured and engineering plates; the cool and SuperTack plates keep the stock value unless the entry lists an exception.
- The PLA entries set the softening temperature to 45 so that the P2S uses its PLA cooling mode.
- The HIPS and ASA entries carry a chamber target. Chamber control stays off in the preset because it would also send chamber commands to the P2S and U1. The X-Max 4 start G-code reads the value (see below).
- Bambu Studio and QIDI Studio have no Orca filament library, so `src/gen_bambu.py` points the same presets at filaments those apps ship (the `bambu` and `qidi` entries in `config/filaments.json`). The Bambu copies are marked compatible with the three P2S nozzles, the QIDI copies with the three X-Max 4 nozzles.

## "(LAN)" printer presets

Source: `src/gen_machine.py` (Orca, in the `orca-machines` zip under AGPL-3.0-only, because their start G-code is copied from OrcaSlicer's stock profiles) and `src/gen_snapmaker.py` (Snapmaker Orca). Orca stores a printer's network address inside a user printer preset, so each networked printer gets a copy of its stock preset named `<stock name> (LAN)`, one per nozzle. Each copy holds the address from `config/printers.json` (release zips: none, set yours in the preset's `print_host` field) and the printer fixes below. Print presets that list the stock printer stay compatible with these copies.

Bed temperature in jobs with several filaments, per slicer:

- OrcaSlicer: the "(LAN)" printers set the bed to follow the filament printed first (a PLA part gets the PLA bed) instead of the default, the hottest filament in the job.
- Snapmaker Orca: the bed takes the highest first-layer bed temperature of all filaments in the job. The fork has no setting for this, so the bed rule the "(LAN)" printers write has no effect there (it is removed in a later release). A job with PLA and PETG therefore starts at 75 C. Give large PLA parts in such a job a per-object outer brim (5 mm) and elephant-foot compensation.

**Snapmaker U1 in OrcaSlicer**

- The start G-code sets the Top Cover purifier mode from the softening temperature of the filaments (cooling up to 50 C, weaker cooling up to 70 C, otherwise keep warm). Without the cover the firmware ignores the command and the print continues.
- The start G-code waits up to 180 s for the chamber target before homing Z, as Snapmaker's own profile does.
- Bed mesh probes 5 mm around the part.
- 0.4 nozzle: retraction 1.5 mm at 30 mm/s, Snapmaker's current default.
- 0.6 and 0.8 nozzle: Orca 2.4.2's stock presets for these are a generic five-tool printer without Snapmaker's tool-change G-code. The copies take the G-code of the 0.4 preset and set four tools with Snapmaker's retraction, z-hop, wipe, clearance and tool-change values.

**Snapmaker U1 in Snapmaker Orca**: Snapmaker's fork already has the tool-change G-code, purifier logic and retraction, so its "(LAN)" printers only add the address and the 5 mm mesh margin (and the bed rule above, which the fork ignores). Print presets use the fork's stock parents.

**Qidi X-Max 4 in OrcaSlicer**: the start G-code is changed so that

- the chamber target is the hottest chamber value of all filaments in the job (stock: first filament only);
- the chamber is never heated when a filament with a softening temperature of 50 C or less (PLA, TPU) is in the job, and the exhaust runs instead;
- the exhaust fan speed uses the 0 to 255 value QIDI's macro expects (the raw percentage gave about 27 % exhaust).

**Bambu P2S and QIDI Studio**: Bambu Studio and QIDI Studio get print and filament presets only. Settings those apps do not know are dropped when the presets are ported (`src/gen_bambu.py` prints the list on build), and Orca's "only one wall on top" option is mapped to its Bambu Studio equivalent.

## Limits

- The presets match the slicer versions in the [README](../README.md#setup). Other versions may report a missing parent preset (unverified).
- Temperatures and drying advice in the filament notes come from the makers' data sheets and are starting points for your own spool.
