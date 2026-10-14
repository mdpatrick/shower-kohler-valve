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
| Saved factory/proposed positions agree with CAD; factory view retains captured wall and separate diverter; GLB excludes display-state copies | `scene_state_check.json`, `tests/blender_states.py` |
| Separate Blender annotations remain visible through duplicate-name import, save and reopen | `annotation_check.json`; `tests/blender_notes.py` uses a disposable fixture |
| Local browser GLB, controls, desktop/mobile layout, JSON download/persistence, linked assets; known-part orientation and CAD/display placement | `browser_check.json` |
| Import validation, explicit corrections/history, rejection without writes, inch conversion, derived relations; uniform transform; actual PDF two-axis calibration; DXF content | `tests/test_measurement_import.py`, `tests/test_geometry_snapshot.py` — 16 tests passed after the diverter/factory-state supplement |
| PDF render/visual inspection | All worksheet, drawing, tiled-template and draft-manual pages rendered; overflowing worksheet fixed; nine-page final worksheet |

The installed frame is right-handed. One uniform scale and rigid orientation align the raw wall reference; no nonuniform stretch or plate-scan fit is used. CAD millimeters map to Blender meters as `(X,-Z,Y)/1000`; glTF maps to browser `(X,Y,Z)/1000`. Browser checks use actual loaded world-space vertices/bounds, including the known-size part's offset hole and clipped corner.

The review initially exposed a missing local Three.js dependency. It was bundled and browser checks then passed with no page errors or failed requests. The desktop was tested at 1440 × 1000 and the mobile page at 390 × 844 without horizontal page overflow. Static project views remain available if another machine cannot use WebGL.

The initial Blender sandbox launch crashed before scene processing. The existing native application worked in its ordinary process environment; all published renders use CPU. No system Python, application or security settings were replaced. The selected scene contains one full primary capture (material groups may be separate objects), a display proxy, raw unregistered secondary captures and parametric display geometry. Packed textures make the selected snapshot self-contained.

Native desktop inspection completed on 2026-10-14 after the user unlocked the Mac and authorized coordination with the house-model chat. That chat reported saving a recovery checkpoint and closing its own Blender instance. The shower scene was reopened through Blender File Open with Load UI enabled and Trusted Source left disabled. The textured scan, coverage outlines, named source/reference collections, new diverter/factory collections and saved camera framing were visibly present. The earlier unrelated unsaved house scene was not discarded or edited by this project. Saved-file state checks and renders were separately verified headlessly; browser tests use an isolated context.

Source limits: the primary mesh preserves the actual opening, visible cuts and hardware at capture, but absolute scale, reflective tips, hidden axes and unseen defects are unverified. Plane residuals measure consistency of chosen intact-stone patches. Both secondary plate scans were viewed in three directions and show severe reflective folding; no reliable whole-part, face, thickness or gasket registration was established. The selected review includes their assessment views; the source ZIPs retain every original texture and triangle.

Coverage uses traced projected contours. The mesh/plate slice uses full-resolution vertices but does not certify triangle crossings or hidden geometry. Provisional exact-solid intersections test the assumed geometry, not the installation. All physical checks remain UNRESOLVED; there is no selected repair, material system, independent fabrication review, physical dry fit, manufacture or water-performance result.

The clean-checkout rebuild passed at commit `8899909`: all three full committed archive blobs and 55 snapshot files matched their hashes, a fresh environment installed all 49 locked packages from the local cache, and the complete CAD/Blender/HTML/PDF build ran without Downloads. Recomputed resolved geometry exactly matched the source checkpoint and accepted canon stayed unchanged. See `restore_check.json`.

The final handoff's bundle-clone receipt is saved beside the bundle as `build/handoff/bundle-restore-receipt.json`, with its bundle hash and source commit. Keeping that receipt outside the bundle avoids a circular requirement that a bundle contain the result of restoring itself. Local cloning and bundles protect recoverability on this machine; they are not off-machine backup or remote publication.

The R001 supplement records OBS-POST-SCAN-01 (user reports no changes), adds a separate diverter tip/nominal trim, corrects the main handle long-reach interpretation, and provides factory versus proposed component poses. The original uniform transform and four original landmarks match the prior checkpoint exactly. POST-SCAN-STATE can pass as a user-report receipt only; every fit, support, sealing and manufacturing decision remains unresolved. The separate diverter landmark is not a fitting input.


## Depth review correction, 2026-10-14

The user flagged the impossible seated-cover rendering. This checkpoint explicitly rejects both trial assembly states. New exact OCCT checks include both studs, both nuts, the inner plate and both valve envelopes against the cover, in original-wall and added-plate placements. The two stud intersections are positive; the lower valve placeholder also conflicts and remains an unmeasured shape assumption. Nut/inner-plate nonintersection is not a physical fit approval. See `deliverables/current/analysis/depth_stack.json` and `docs/decisions/depth_review_2026-10-14.md`.

Executed after this correction: 17 unit/snapshot tests; desktop/mobile browser tests with visible fit warnings, unchanged studs, depth-case switching and stud-section navigation; saved Blender scene reopened and placements/view exclusions checked; all 21 PDF pages rendered and visually inspected, including the new seventh manual page. No page errors or failed local requests. Original archives and current deliverable hashes passed validation against committed evidence. The registration, measurement canon, all scan-derived part positions, and all 15 reference-solid bounds/volumes exactly match checkpoint `dbaa438` (apart from harmless floating point volume tolerance).

The existing in-app browser was refreshed and visibly opened at Depth & sealing. Its response still contained no physical readings. The native Blender scene was reloaded from the latest saved file without an unsaved-change prompt. No user data or measurements were imported by the isolated UI tests.

The first warning-stamp render attempt exposed a Blender property-name error. It was corrected to `stamp_note_text`; all 13 views then rendered and the saved file reopened. The command wrapper now supplies `--python-exit-code 1` so Python exceptions cannot silently yield a successful stage exit.


## Control-depth inquiry, 2026-10-14

The user's excessive-stud-projection, rear wood-contact and connected-plumbing reports are preserved as qualitative observations. The nominal upper bare-stem comparison is conditional on identifying the same tip and applicable revision. Check 10 records separate control block/gap readings and tip/adapter identity; signed projections remain diagnostic and do not move the valve geometry. Check 09 and the contractor schedule now include rear fastener identity, usable stud travel, independent rough-in datum and adapter/handle seating.

Executed: 21 unit/import/snapshot tests passed, including recessed control tips, independent setup heights, and protection against treating a plausible unidentified tip as a fit pass. The isolated browser verified all new fields and identity notes in JSON download and local persistence, desktop/mobile layout and linked assets, with no page errors or failed requests. The saved Blender file reopened and passed component-placement and view-state checks. No synthetic values were imported into the actual canon.

All 23 PDF pages were rendered and visually inspected as a contact sheet, with full-page checks of worksheet 09/10 and manual 02/08. After the final caption edit, 22 raster pages were pixel-identical to the inspected set and the remaining worksheet page 10 was inspected again. The new observed side-view annotation and browser explanation were visually checked. The accepted measurements, registration, all resolved component positions, and all 15 CAD solids' bounds, volumes and trial poses match checkpoint `a2b285b`. See `control_depth_check.json`. The build reused unchanged CAD/Blender stages after review-only corrections. Physical depth, repair choice, fit, fabrication approval and water performance remain unresolved.
