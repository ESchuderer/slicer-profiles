# Install the presets

Download `slicer-profiles-bambu-<version>.zip` from the [latest release](https://github.com/ESchuderer/slicer-profiles/releases/latest) and import it into Bambu Studio. It holds the print and filament presets for the Bambu Lab H3C; every preset is listed in [catalog.md](catalog.md), and `NOTICE.md` in the release names its license.

## Check the download

Each release also carries `SHA256SUMS` and `manifest.json` (every preset with its checksum and license). In the download folder:

```
sha256sum --ignore-missing -c SHA256SUMS
```

## Import

1. In Bambu Studio, choose **File > Import > Import Configs**.
2. Select the zip, or the JSON files from inside it, and confirm.
3. Restart Bambu Studio if the new presets do not show up.

## Fallback: unzip into the preset folder

If the import refuses the zip, close Bambu Studio, unzip into its user preset folder and start it again. The zip holds `process/` and `filament/`; both must land directly in the preset folder, `~/.config/BambuStudio/user/default/` on Linux (tested). When you are logged in, use the folder `user/<account id>/` that the app loads (`preset_folder` in `~/.config/BambuStudio/BambuStudio.conf`) instead of `default`; presets there may sync to Bambu's cloud. Windows and macOS keep the same folder in the app's data directory (unverified: `%APPDATA%\BambuStudio\` and `~/Library/Application Support/BambuStudio/`).

```
cd ~/.config/BambuStudio/user/default
unzip -o ~/Downloads/slicer-profiles-bambu-v0.2.0.zip
```

## After the import

- Choose the stock `Bambu Lab H3C <size> nozzle` printer; the presets show for the nozzles they are made for.
- The presets inherit from Bambu Studio's stock profiles by name. They match the version in the [README](https://github.com/ESchuderer/slicer-profiles/blob/main/README.md); other versions may report a missing parent preset (unverified).
