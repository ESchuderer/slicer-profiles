# Install the presets

Download the zip for your slicer from the [latest release](https://github.com/ESchuderer/slicer-profiles/releases/latest), close the slicer, unzip into its user preset folder and start it again.

| Slicer | Zip | Presets for |
|---|---|---|
| OrcaSlicer | `slicer-profiles-orca-<version>.zip` | Bambu Lab P2S, Snapmaker U1, Qidi X-Max 4 |
| Bambu Studio | `slicer-profiles-bambu-<version>.zip` | Bambu Lab P2S |
| QIDI Studio | `slicer-profiles-qidi-<version>.zip` | Qidi X-Max 4 |
| Snapmaker Orca | `slicer-profiles-snapmaker-<version>.zip` | Snapmaker U1 |

Each zip holds `process/`, `filament/` and, for Orca and Snapmaker Orca, `machine/`. Unzip so these folders land directly in the preset folder:

| Slicer | Preset folder (Linux, tested) |
|---|---|
| OrcaSlicer | `~/.config/OrcaSlicer/user/default/` |
| Bambu Studio | `~/.config/BambuStudio/user/default/` |
| QIDI Studio | `~/.config/QIDIStudio/user/default/` |
| Snapmaker Orca | `~/.config/Snapmaker_Orca/user/default/` |

When you are logged in to a slicer account, use the folder `user/<account id>/` that the app loads (`preset_folder` in `~/.config/<app>/<app>.conf`) instead of `default`.
Windows and macOS: the same `user/default/` folder lives in the app's data directory (unverified: `%APPDATA%\<app>\` and `~/Library/Application Support/<app>/`).

```
cd ~/.config/OrcaSlicer/user/default
unzip -o ~/Downloads/slicer-profiles-orca-v0.1.0.zip
```

## After the import

- Select the "(LAN)" printers in Orca and Snapmaker Orca. They carry the printer fixes and the example address `192.0.2.x`: set your printer's address in the preset's `print_host` field (Device tab).
- The presets inherit from each slicer's stock profiles by name. They match the slicer versions in the [README](../README.md#setup); other versions may report a missing parent preset (unverified).
- Generate your own set with your addresses and filaments instead: [README](../README.md#build-your-own).
