# Measured outer-cover update — R004

**The prior seated-cover assembly is rejected: unchanged stud envelopes intersect the assumed cover. The review now shows the depth conflict explicitly. No repair is selected. All geometry is DRAFT / NOT FOR FABRICATION.** Twelve physical plate/foam readings are accepted, with one derived upper-opening position. Dry fit, fabrication approval, incoming-part inspection and installed water testing remain unperformed.

Open the review with `./project review` from this directory. It serves only `deliverables/current` on localhost. Use the static illustrated views if WebGL is unavailable. The twelve measurement groups include raw-reading fields and a JSON download; filling the page saves in that browser only and does not change CAD.

| Open or read | Repository path |
|---|---|
| Local HTML review | `deliverables/current/review/index.html` (launch through `./project review`) |
| Blender inspection workspace | `deliverables/current/blender/installation_R004_DRAFT.blend` |
| Twelve-page tailored worksheet | `deliverables/current/drawings/measurement_worksheet_R004.pdf` |
| Conditional fit and coverage results | `deliverables/current/analysis/checks.json` |
| Contractor inspection/adjustment schedule | `deliverables/current/analysis/contractor_schedule.json` |
| Draft repair sequence | `deliverables/current/manual/index.html` and `repair_manual_R004_DRAFT.pdf` |
| Draft profile drawing / calibrated tiled template | `deliverables/current/drawings/candidate_drawing_R004_DRAFT.pdf` / `profile_template_R004_DRAFT.pdf` |
| Separate reference STEP, candidate STEP/DXF, assembly STEP | `deliverables/current/cad/` |
| Snapshot hashes, source hash, readiness | `deliverables/current/manifest.json` |
| Reviewer entry point | `docs/downstream_audit_prompt.md` |

The user identified **K-T14489-4-BN**, **K-T14491-4-BN**, **K-2973-KS-NA** and the separate **K-737-K-NA** diverter. See [the parts record](docs/verified_kohler_parts.md). On 2026-10-14 the user confirmed **nothing has changed since capture**: piping, valve pose, stud adjustment and wall opening remain as captured by user report. See [the current-state record](docs/decisions/current_state_2026-10-14.md). Some inner-plate dimensions are now measured; the free plate depth and approximate foam section are recorded; installed valve depths, gasket footprint/compression and hardware revision remain unverified.

Evidence priority is feature-specific: accepted physical observations govern the actual installation; the wall/valve scan governs captured spatial relationships; applicable manufacturer dimensions establish nominal design; locally credible secondary scan features can corroborate; visible assumptions fill remaining gaps. Neither plate scan is used for dimensional registration. Their severe reflective distortion does not justify flattening or averaging them into the primary scan.

The conditional scale uses the documented nominal 3⅛-inch control spacing. It is **not physically calibrated**. The fitted intact-stone plane has about 0.23 mm local residual RMS at that scale; this is not an absolute accuracy claim. The origin is the lower observed tip projected onto that plane, with +X right, +Y up and +Z out. The scan's valve pose and damage remain unchanged.

The limiting traced cut is CUT-03. The 8-inch circle has approximately **0.51 mm** projected margin there before a **1.5 mm tracing allowance**, with scale and placement uncertainty still unbounded. A 230 mm comparison profile is exploratory. Its single clearance aperture conflicts with the assumed factory gasket path. Neither size is a selected repair or demonstrated fit. See [questions answered](docs/questions_answered.md).

The separate lower diverter is now represented by a nominal 98.425 mm trim envelope at its scan-estimated tip center. The 230 mm candidate has about 11.0 mm projected gap to that trim, with unbounded scale/placement uncertainty. Nominal full-rotation handle reach circles overlap; actual permitted travel and depth must be checked physically. The original scan and registration are unchanged. The original-wall and added-plate trials use explicit separate positions, but both conflict with unchanged hardware. They are diagnostic views, not feasible assembled states. See [the depth correction](docs/decisions/depth_review_2026-10-14.md) and the review’s Depth & sealing section.

Earlier depth inquiry: the user confirms excessive stud projection and reports rear bolt contact with wood. These are qualitative observations; no numerical readings were accepted. A conditional comparison of the upper scan tip with the valve specification also flags rough-in depth for checking, subject to bare-stem identification. See [the observation and research record](docs/physical_checks/depth_inquiry_2026-10-14.json). This discussion does not select stud cutting, wood drilling or valve relocation.

The prior R002 update used the actual front-face photo: 130.35 mm width, 6.5 inch height, 48.46 mm upper opening, 18 mm top gap, 5.66 mm SW hole, 106.39 mm nearest-edge diagonal gap and 11.71 mm NE hole-edge-to-rim gap. The NE diameter and lower large opening remain unmeasured. Center spacing 112.05 mm is conditional on equal 5.66 mm mounting holes. The metal outline is rounded rectangular; corner geometry, formed depth and installed placement remain provisional. Front metal dimensions do not establish rear gasket dimensions. See [the measurement record](docs/physical_checks/inner_plate_2026-10-14.json).

R003 also records 15.44 mm from uncompressed rear foam to frontmost metal, approximately 6 mm free foam thickness and approximately 6 mm representative band width. The model matches that free envelope with its metal origin provisionally at the foam backing. The approximately 9.4 mm difference is not sheet thickness or an accepted rear-metal-land depth. The minimum band width, rear footprint, installed compression, local nut seats and actual cover cavity remain unmeasured. See [the free-depth record](docs/physical_checks/inner_plate_foam_2026-10-14.json).

The R004 outer-cover photo confirms the outward face, 7.25 inch (184.15 mm) diameter by tape, and 33.79 mm upper opening by caliper. The upper bore replaces the old 36 mm placeholder. The 46.25 mm blue gap and 35.23 mm orange rim gap are preserved as reported annotations; their exact contact edges await clarification. Lower bore diameter, opening positions and rear cavity remain unmeasured. No captured hardware or wall registration changes. See [the outer-cover record](docs/physical_checks/outer_plate_2026-10-14.json).

Next: complete Checks 11 and 12 and read Depth & sealing in the review, then take Checks 01–08. Prioritize Checks 04–07 and the new focused Check 10 for inner formed depth, foam, each local cover cavity, stud projection and control-tip identity/depth. The most consequential readings are control spacing, inner plate datums and opening edges, actual gasket path, outer trim registration/cavity, and separate stud depths. Describe differences from the amber reference shapes instead of trying to make readings match them. Check 09 assigns inaccessible plumbing, backing and neighboring handle/tool-access observations to the installer. Report only new changes after the current-state confirmation. Return new readings using R004; reconcile any older response before importing; the new M10 readings are diagnostic and cannot move the valve without tip-identity review. The scan registration and captured hardware are unchanged.

```sh
./project doctor
./project review
./project import-measurements /absolute/path/to/shower-readings-R004.json --dry-run
./project import-measurements /absolute/path/to/shower-readings-R004.json
./project build
./project validate
```

An import checks project/revision/IDs/units, preserves prior observations and conflicts, archives the response, increments the revision and invalidates fit readiness. It does not grant fabrication approval. Review changed conclusions before making an accepted-measurement Git checkpoint.

Blender view layers include **Observed, Coverage, Original_wall_trial, Trial_fit_CONFLICT, Exploded, Inner, Gasket, Section_controls, Section_studs, Full_source, CAD_only**. Named cameras are in `07_CAMERAS_AND_LIGHTS`, including original-wall trial, neighbor clearance and CAM_07_Observed_control_depth (use the Observed view layer). One full-resolution primary scan and packed textures are retained; an explicitly labeled decimated copy is used for display. Amber reconstructed metal, pink gasket and green new seal band are provisional. Original-wall comparison, exploded and section copies never enter the proposed assembly export. Save personal annotations as a separate `user_notes.blend` with a `USER_NOTES` collection; the builder reloads it. Changed generated files are backed up to `deliverables/manual_edits/` before a rebuild.

For restoration and dependencies, see [environment/README.md](environment/README.md) and [validation record](docs/validation/README.md). Complete original ZIPs are ordinary Git blobs. No LFS, remote, upload, order or trade contact is involved. `./project handoff` creates a private local Git bundle and compact review ZIP. **Local Git and a local bundle are not off-machine backups.**

The final repair, material schedule, physical verification and independent adversarial review remain future gates. Preserve travertine; no cutting, grinding, drilling, enlargement or retiling has been authorized. Keep the original inner plate, gasket, drainage and service functions.
