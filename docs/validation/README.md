# Executed validation at the first reconstruction checkpoint

These results distinguish software/evidence checks from the unperformed physical work. Generated check files carry the working revision. No measurement entered in a synthetic test was imported into the real canon.

| Executed check | Evidence |
|---|---|
| Original ZIP copy sizes/SHA-256; full committed Git bytes read back | `canon/inputs.json`, `latest_integrity.json` |
| Original evidence commit and clean local clone extraction | Initial commit `1f817e1`; `build/restore-test` used only repository inputs |
| Git object integrity | `git fsck --full` |
| Known 100 × 60 × 4 mm CAD part, off-center hole, asymmetric NE corner; STEP/STL reimport | `coordinate_cad_check.json` |
| Blender dimensions, hole/marker orientation, CPU render, save and reopen | `coordinate_blender_check.json` |
| CAD solids and exported STEP validity, bounds/volume; nonfused assembly count; clean mm DXF with one aperture | `deliverables/current/cad/cad_manifest.json` |
| Packed scene assets, source/proxy separation, saved scene reopened | `deliverables/current/blender/scene_check.json` |
| Separate Blender annotations remain visible through duplicate-name import, save and reopen | `annotation_check.json`; `tests/blender_notes.py` uses a disposable fixture |
| Local browser GLB, controls, desktop/mobile layout, JSON download/persistence, linked assets; known-part orientation and CAD/display placement | `browser_check.json` |
| Import validation, explicit corrections/history, rejection without writes, inch conversion, derived relations; uniform transform; actual PDF two-axis calibration; DXF content | `tests/test_measurement_import.py`, `tests/test_geometry_snapshot.py` — 14 tests passed |
| PDF render/visual inspection | All worksheet, drawing, tiled-template and draft-manual pages rendered; overflowing worksheet fixed; nine-page final worksheet |

The installed frame is right-handed. One uniform scale and rigid orientation align the raw wall reference; no nonuniform stretch or plate-scan fit is used. CAD millimeters map to Blender meters as `(X,-Z,Y)/1000`; glTF maps to browser `(X,Y,Z)/1000`. Browser checks use actual loaded world-space vertices/bounds, including the known-size part's offset hole and clipped corner.

The review initially exposed a missing local Three.js dependency. It was bundled and browser checks then passed with no page errors or failed requests. The desktop was tested at 1440 × 1000 and the mobile page at 390 × 844 without horizontal page overflow. Static project views remain available if another machine cannot use WebGL.

The initial Blender sandbox launch crashed before scene processing. The existing native application worked in its ordinary process environment; all published renders use CPU. No system Python, application or security settings were replaced. The selected scene contains one full primary capture (material groups may be separate objects), a display proxy, raw unregistered secondary captures and parametric display geometry. Packed textures make the selected snapshot self-contained.

The final desktop launch was requested, but native-window visual inspection was unavailable while the Mac was locked. Saved-file reopening and renders were verified through Blender itself; the independent browser tests used an isolated context. No lock-screen bypass was attempted.

Source limits: the primary mesh preserves the actual opening, visible cuts and hardware at capture, but absolute scale, reflective tips, hidden axes and unseen defects are unverified. Plane residuals measure consistency of chosen intact-stone patches. Both secondary plate scans were viewed in three directions and show severe reflective folding; no reliable whole-part, face, thickness or gasket registration was established. The selected review includes their assessment views; the source ZIPs retain every original texture and triangle.

Coverage uses traced projected contours. The mesh/plate slice uses full-resolution vertices but does not certify triangle crossings or hidden geometry. Provisional exact-solid intersections test the assumed geometry, not the installation. All physical checks remain UNRESOLVED; there is no selected repair, material system, independent fabrication review, physical dry fit, manufacture or water-performance result.

The clean-checkout rebuild passed at commit `8899909`: all three full committed archive blobs and 55 snapshot files matched their hashes, a fresh environment installed all 49 locked packages from the local cache, and the complete CAD/Blender/HTML/PDF build ran without Downloads. Recomputed resolved geometry exactly matched the source checkpoint and accepted canon stayed unchanged. See `restore_check.json`.

The final handoff's bundle-clone receipt is saved beside the bundle as `build/handoff/bundle-restore-receipt.json`, with its bundle hash and source commit. Keeping that receipt outside the bundle avoids a circular requirement that a bundle contain the result of restoring itself. Local cloning and bundles protect recoverability on this machine; they are not off-machine backup or remote publication.
