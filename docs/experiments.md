# Experiments

Questions the code cannot answer, tried by hand in the slicer. Each result names the app version and the date; a release that depends on one waits for it.

| Id | Question | Needed for | Status |
|---|---|---|---|
| E3 | Does File > Import > Import Configs in Bambu Studio accept a release zip, and a zip that also holds a `NOTICE.md`? | the install page; whether the license notice can go inside the zip | not run |

Until E3 passes, `NOTICE.md` ships beside the zip as a release file, not inside it.

## E3: zip import

App: Bambu Studio at the version in the README.

1. Build the release files: `scripts/release.sh v0.2.0` (files in `dist/`).
2. Make the second test zip: `cp dist/slicer-profiles-bambu-v0.2.0.zip /tmp/e3-notice.zip && zip -j /tmp/e3-notice.zip dist/NOTICE.md`.
3. Close Bambu Studio and copy its user preset folder (see [install.md](install.md)) somewhere safe.
4. Start it, choose File > Import > Import Configs and select the plain zip. Note whether it is accepted, how many presets appear and any message.
5. Close it, restore the copied folder, start it again and import `/tmp/e3-notice.zip`. Note whether it is accepted, refused or the extra file ignored.
6. Close it and restore the copied folder.

| App and version | Date | Plain zip | Zip with `NOTICE.md` |
|---|---|---|---|
| Bambu Studio | | | |
