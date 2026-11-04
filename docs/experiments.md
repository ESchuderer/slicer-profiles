# Experiments

Questions the code cannot answer, tried by hand in the slicers. Each result names the app version and the date; a release that depends on one waits for it.

| Id | Question | Needed for | Status |
|---|---|---|---|
| E3 | Does File > Import > Import Configs accept a release zip, and a zip that also holds a `NOTICE.md`? | the install page; whether the license notice can go inside the zips | not run |
| E4 | Do QIDI Studio and Bambu Studio write the printer address (`print_host`) into a project 3MF? | the print log (project files stay out of git) | not run |
| E5 | Does Snapmaker Orca resolve a preset whose parent has an old name listed in `renamed_from`? | pinning the Snapmaker profile tree | after the pinned upstream trees (next milestone) |

Until E3 passes, `NOTICE.md` ships beside the zips as a release file, not inside them.

## E3: zip import

Apps: OrcaSlicer 2.4.2, Bambu Studio 02.09.01.70, QIDI Studio 02.07.02.73, Snapmaker Orca 2.4.1 (the versions in the README).

1. Build the release files: `scripts/release.sh v0.2.0` (files in `dist/`).
2. Make the second test zip: `cp dist/slicer-profiles-qidi-v0.2.0.zip /tmp/e3-notice.zip && zip -j /tmp/e3-notice.zip dist/NOTICE.md`. Use the zip of each app's own slicer in place of `qidi`.
3. Close the app and copy its user preset folder (see [install.md](install.md)) somewhere safe.
4. Start the app, choose File > Import > Import Configs and select the plain zip. Note whether it is accepted, how many presets appear and any message.
5. Close the app, restore the copied folder, start it again and import `/tmp/e3-notice.zip`. Note whether it is accepted, refused or the extra file ignored.
6. Close the app and restore the copied folder.

| App and version | Date | Plain zip | Zip with `NOTICE.md` |
|---|---|---|---|
| OrcaSlicer | | | |
| Bambu Studio | | | |
| QIDI Studio | | | |
| Snapmaker Orca | | | |

## E4: address in project files

1. QIDI Studio: select the X-Max 4, set a test address `192.0.2.50` in the printer's connection settings. Bambu Studio: add a printer that is connected by address (not a Bambu Lab printer) with `192.0.2.50`.
2. Load `tests/models/cube.stl`, slice, and save the project as `e4.3mf` (File > Save Project As).
3. `unzip -p e4.3mf Metadata/project_settings.config | grep -E '"print_host|"printhost'`
4. Note every key that holds `192.0.2.50`. Remove the test printer afterwards.

| App and version | Date | Address keys in the 3MF |
|---|---|---|
| QIDI Studio | | |
| Bambu Studio | | |
