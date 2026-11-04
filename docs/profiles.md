# What the presets do

The presets are Bambu Studio user presets for the Bambu Lab H3C. Each one inherits a stock H3C preset by name and stores only the values set here; everything else shows as inherited, so vendor updates still reach you. The data lives in `config/h3c.json` and `config/filaments.json`, and the tables on this page are generated from it (`src/docs.py`). Every preset is listed by name in [catalog.md](catalog.md).

## What is in each zip

<!-- generated: zips -->

| Zip | Print presets | Filament presets | License |
|---|---|---|---|
| `bambu` (Bambu Studio) | 12 | 17 | CC-BY-4.0 |

<!-- end generated -->

There are no printer presets: choose the stock `Bambu Lab H3C <size> nozzle` printer and pick the print and filament presets. OrcaSlicer has no H3C profiles yet; its zip returns once a stable OrcaSlicer release ships them.

## Print presets

Print speeds, accelerations and cooling stay at the H3C stock values. Each style changes only the keys below on the stock default print preset of its nozzle:

<!-- generated: parents -->

| Nozzle | Stock print preset the styles build on |
|---|---|
| 0.2 | `0.10mm Standard @BBL H3C 0.2 nozzle` |
| 0.4 | `0.20mm Standard @BBL H3C` |
| 0.6 | `0.30mm Standard @BBL H3C 0.6 nozzle` |
| 0.8 | `0.40mm Standard @BBL H3C 0.8 nozzle` |

<!-- end generated -->

<!-- generated: styles -->

| Style or variant | Nozzle | Changed keys |
|---|---|---|
| Strong | 0.2 | `wall_loops` 5, `sparse_infill_density` 40%, `sparse_infill_pattern` gyroid, `top_shell_thickness` 1.0, `bottom_shell_thickness` 0.8 |
| Strong | 0.4 | `wall_loops` 5, `sparse_infill_density` 40%, `sparse_infill_pattern` gyroid, `top_shell_thickness` 1.4, `bottom_shell_thickness` 1.2 |
| Strong | 0.6 | `wall_loops` 4, `sparse_infill_density` 40%, `sparse_infill_pattern` gyroid, `top_shell_thickness` 1.6, `bottom_shell_thickness` 1.2 |
| Strong | 0.8 | `wall_loops` 3, `sparse_infill_density` 40%, `sparse_infill_pattern` gyroid, `top_shell_thickness` 1.8, `bottom_shell_thickness` 1.4 |
| MM-Support | all | `enable_support` 1, `support_type` normal(auto), `support_top_z_distance` 0, `support_bottom_z_distance` 0, `support_interface_top_layers` 3, `support_interface_bottom_layers` 3, `support_interface_spacing` 0, `support_interface_pattern` rectilinear_interlaced, `support_interface_filament` 2, `support_base_pattern` rectilinear-grid, `support_object_xy_distance` 0.3, `independent_support_layer_height` 0 |

<!-- end generated -->

- **Strong**: more walls, 40 % gyroid infill and thicker top and bottom shells, for parts that carry load.
- **MM-Support**: normal supports with the base in the object's own filament and the interface layers from filament 2, for example PLA under PETG, with zero Z gap; the stock prime tower stays on. Use it when two materials that do not bond print together.

Names read `<layer>mm <style> @H3C <nozzle>`, for example `0.20mm Strong MM-Support @H3C 0.4`. Each value is written once per hotend slot of the stock preset (Standard, High Flow and TPU 2.85 mm), so every hotend gets it.

## Filament presets

Third-party filaments without an H3C stock preset. Each preset inherits the H3C Generic preset of its material for the nozzle; where the stock tree has a separate Generic preset for a nozzle, the filament gets a separate preset for it.

<!-- generated: filaments -->

| Preset | Material | Stock parent | Nozzles |
|---|---|---|---|
| SUNLU PLA+ 2.0 HQ 0.2 nozzle | PLA | `Generic PLA @BBL H3C 0.2 nozzle` | 0.2 |
| SUNLU PLA+ 2.0 HQ | PLA | `Generic PLA @BBL H3C` | 0.4, 0.6, 0.8 |
| SUNLU PLA Matte HQ 0.2 nozzle | PLA | `Generic PLA @BBL H3C 0.2 nozzle` | 0.2 |
| SUNLU PLA Matte HQ | PLA | `Generic PLA @BBL H3C` | 0.4, 0.6, 0.8 |
| SUNLU PETG 2.0 HQ 0.2 nozzle | PETG | `Generic PETG @BBL H3C 0.2 nozzle` | 0.2 |
| SUNLU PETG 2.0 HQ | PETG | `Generic PETG @BBL H3C` | 0.4, 0.6, 0.8 |
| eSUN PETG HQ 0.2 nozzle | PETG | `Generic PETG @BBL H3C 0.2 nozzle` | 0.2 |
| eSUN PETG HQ | PETG | `Generic PETG @BBL H3C` | 0.4, 0.6, 0.8 |
| SUNLU HS Matte PETG HQ 0.2 nozzle | PETG HF | `Generic PETG HF @BBL H3C 0.2 nozzle` | 0.2 |
| SUNLU HS Matte PETG HQ | PETG HF | `Generic PETG HF @BBL H3C 0.4 nozzle` | 0.4, 0.6, 0.8 |
| CC3D HIPS HQ 0.2 nozzle | HIPS | `Generic HIPS @BBL H3C 0.2 nozzle` | 0.2 |
| CC3D HIPS HQ | HIPS | `Generic HIPS @BBL H3C 0.4 nozzle` | 0.4, 0.6, 0.8 |
| Anycubic ASA HQ 0.2 nozzle | ASA | `Generic ASA @BBL H3C 0.2 nozzle` | 0.2 |
| Anycubic ASA HQ | ASA | `Generic ASA @BBL H3C 0.4 nozzle` | 0.4, 0.6, 0.8 |
| SUNLU ASA HQ 0.2 nozzle | ASA | `Generic ASA @BBL H3C 0.2 nozzle` | 0.2 |
| SUNLU ASA HQ | ASA | `Generic ASA @BBL H3C 0.4 nozzle` | 0.4, 0.6, 0.8 |
| SUNLU TPU 95A HQ | TPU | `Generic TPU @BBL H3C` | 0.4 |

<!-- end generated -->

Each preset sets the maker's nozzle temperatures and range, and the density where a source gives it. Every other value, the chamber target included, comes from the H3C Generic parent, unless a data sheet or a filament database (named in the preset's notes) gives a number. ASA heats the chamber to the stock 60 C; HIPS keeps the stock chamber off. The Notes tab carries the maker's data sheet values and drying advice.

## Limits

- The presets match the Bambu Studio version in the [README](https://github.com/ESchuderer/slicer-profiles/blob/main/README.md). Other versions may report a missing parent preset (unverified).
- Temperatures and drying advice come from the makers' data sheets and are starting points for your own spool.
