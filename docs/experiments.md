# Experiments

Questions the code cannot answer, tried by hand in the slicer. Each result names the app version and the date; a release that depends on one waits for it.

| Id | Question | Needed for | Status |
|---|---|---|---|
| E3 | Does File > Import > Import Configs in Bambu Studio accept a release zip, and a zip that also holds a `NOTICE.md`? | the install page; whether the license notice can go inside the zip | not run |

Until E3 passes, `NOTICE.md` ships beside the zip as a release file, not inside it.

## E3: zip import

App: Bambu Studio at the version in the README, with the stock Bambu Lab H3C printer added for the 0.2, 0.4, 0.6 and 0.8 mm nozzles (the import skips a preset whose stock parent it cannot find).

1. Build the release files: `scripts/release.sh v0.2.0` (files in `dist/`).
2. Make the second test zip: `cp dist/slicer-profiles-bambu-v0.2.0.zip /tmp/e3-notice.zip && zip -j /tmp/e3-notice.zip dist/NOTICE.md`.
3. Close Bambu Studio and copy its user preset folder (see [install.md](install.md)) somewhere safe.
4. Start it, choose File > Import > Import Configs and select the plain zip. If it asks to overwrite a preset of an earlier install with the same name, choose Yes to All and note it. Note the "Import result" message and whether `0.20mm Strong @H3C 0.4` and `SUNLU PLA+ 2.0 HQ` show for the H3C 0.4 nozzle printer.
5. Import `/tmp/e3-notice.zip` the same way, with Yes to All at the overwrite prompt (the presets of step 4 exist now). Note the message and whether it is accepted, refused or the extra file ignored.
6. To undo the import, close Bambu Studio and restore the copied folder.

Expected from the source of Bambu Studio 02.09.01.70 (`MainFrame::load_config_file` in [MainFrame.cpp](https://github.com/bambulab/BambuStudio/blob/v02.09.01.70/src/slic3r/GUI/MainFrame.cpp), `PresetBundle::import_presets` in [PresetBundle.cpp](https://github.com/bambulab/BambuStudio/blob/v02.09.01.70/src/libslic3r/PresetBundle.cpp)): the file dialog takes `.zip`; every member is read as a preset by its file name, a member that is not a preset (such as `NOTICE.md`) is skipped, and the message reads "There are 29 configs imported." for both zips.

| App and version | Date | Plain zip | Zip with `NOTICE.md` |
|---|---|---|---|
| Bambu Studio | | | |
