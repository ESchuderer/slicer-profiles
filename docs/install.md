# Install the presets

Download the zip for your slicer from the [latest release](https://github.com/ESchuderer/slicer-profiles/releases/latest) and import it.

| Slicer | Zip | Presets for |
|---|---|---|
| OrcaSlicer | `slicer-profiles-orca-<version>.zip` | Bambu Lab P2S, Snapmaker U1, Qidi X-Max 4 |
| OrcaSlicer, "(LAN)" printers | `slicer-profiles-orca-machines-<version>.zip` (AGPL-3.0-only) | Snapmaker U1, Qidi X-Max 4 |
| Bambu Studio | `slicer-profiles-bambu-<version>.zip` | Bambu Lab P2S |
| QIDI Studio | `slicer-profiles-qidi-<version>.zip` | Qidi X-Max 4 |
| Snapmaker Orca | `slicer-profiles-snapmaker-<version>.zip` | Snapmaker U1 |

Every preset in each zip is listed in [catalog.md](catalog.md). `NOTICE.md` in the release names the license of each zip.

## Check the download

Each release also carries `SHA256SUMS` and `manifest.json` (every preset with its checksum and license). In the download folder:

```
sha256sum --ignore-missing -c SHA256SUMS
```

## Import

1. In the slicer, choose **File > Import > Import Configs**.
2. Select the zip, or the JSON files from inside it, and confirm.
3. Restart the slicer if the new presets do not show up.

## Fallback: unzip into the preset folder

If the import refuses the zip, close the slicer, unzip into its user preset folder and start it again. The zips hold `process/` and `filament/`; `orca-machines` and `snapmaker` also hold `machine/`. These folders must land directly in the preset folder, so for OrcaSlicer unzip both the `orca` and the `orca-machines` zip there:

| Slicer | Preset folder (Linux, tested) |
|---|---|
| OrcaSlicer | `~/.config/OrcaSlicer/user/default/` |
| Bambu Studio | `~/.config/BambuStudio/user/default/` |
| QIDI Studio | `~/.config/QIDIStudio/user/default/` |
| Snapmaker Orca | `~/.config/Snapmaker_Orca/user/default/` |

When you are logged in to a slicer account, use the folder `user/<account id>/` that the app loads (`preset_folder` in `~/.config/<app>/<app>.conf`) instead of `default`. Presets there may sync to the vendor's cloud.
Windows and macOS: the same `user/default/` folder lives in the app's data directory (unverified: `%APPDATA%\<app>\` and `~/Library/Application Support/<app>/`).

```
cd ~/.config/OrcaSlicer/user/default
unzip -o ~/Downloads/slicer-profiles-orca-v0.2.0.zip
unzip -o ~/Downloads/slicer-profiles-orca-machines-v0.2.0.zip
```

## After the import

- Select the "(LAN)" printers in Orca (from the `orca-machines` zip) and Snapmaker Orca. They carry the printer fixes and no address: set your printer's address in the preset's `print_host` field (Device tab).
- The presets inherit from each slicer's stock profiles by name. They match the slicer versions in the [README](https://github.com/ESchuderer/slicer-profiles/blob/main/README.md); other versions may report a missing parent preset (unverified).
- Generate your own set with your addresses and filaments instead: [README](https://github.com/ESchuderer/slicer-profiles/blob/main/README.md).
