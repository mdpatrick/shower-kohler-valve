# CB01 - concentric circular escutcheon preparation

**Latest: AP01 upright aperture and handle access (October 15).** Open the [access comparison](deliverables/current/fabrication/aperture-access/index.html), [four-page PDF with full-size templates](deliverables/current/fabrication/aperture-access/aperture_access_AP01_DRAFT.pdf), or [small Blender access workspace](deliverables/current/fabrication/aperture-access/aperture_access_AP01_DRAFT.blend). The recommended next dry-fit opening is an upright 116.35 x 151.10 mm rounded rectangle, R33, centered on the provisional inner-plate center. Separate draft CAD covers both existing circular main outer diameters (220 / 214.15 mm) and both metal thickness trials (1.524 / 3.175 mm). The old diagonal aperture was a buffered scan-hardware convex hull, not a factory-required opening or a handle-fit proof. AP01 contains it with 0.446 mm minimum extra gap, clears all 51,929 tested forward triangle projections and contains the measured upper inner-opening footprint with 11.0 mm nominal margin. This does not establish hidden adapter, spline, thread or axial engagement. The whole knob installs from the front; its rearward-reaching connection still needs actual clearance and engagement.

**Latest accepted clarification:** the removed inner plate's foam meets the outer metal edge, and the user confirms the 4.56-inch rods meet the wood. Conditional wood clearance holes are the user's authorized preferred remedy if stud retraction is needed and other valve/handle depth checks pass. This supersedes earlier uncertainty about contact and blanket statements below that wood drilling is unselected; relief dimensions remain unspecified and tile changes remain prohibited. [Accepted observation](docs/physical_checks/foam_edge_and_access_2026-10-15.json). With the approximate 6 mm band and assumed R40 corners, AP01 leaves 1 mm nominal extra land inside the foam, not an accepted tolerance. Exact corners, minimum band width, alignment and compression remain open.

Rebuild with `./project prepare-aperture`. AP01 is separate from the historical CB01/LOC01 and F005 quote CAD. **Do not send the older quote ZIPs as the new upright-aperture design.** No physical test, final design selection, material/finish approval, order or manufacturing release follows from this study.

**Factory stud and foam clarification (October 15):** [Rear review: gasket and stud dimensions](deliverables/current/review/rear/index.html#foam-and-studs). Kohler's two-control parts diagram identifies stud 1038645; its product specification is 10-24 × 4.56 in (115.8 mm nominal full length). This is separate from the 7/16 in (11.1 mm) original-wall projection limit. Existing scan tips imply about 15.5 / 19.6 mm inward travel to that limit, conditionally; no wood depth or drilling dimension is established. The foam is the removable inner plate's perimeter gasket, not material currently in the exposed cavity. [Source and assumption record](docs/physical_checks/foam_and_stud_research_2026-10-15.json).

**Current rear evidence (REAR01, October 15):** the foam-backed factory inner plate is removed; no foam is installed at this exposed-valve stage. Open [the updated Blender review](deliverables/current/blender/installation_REAR01_DRAFT.blend), which opens to the supplied rear photographs and includes a separate front-scan-only scene. [Rear photo review](deliverables/current/review/rear/index.html) explains the apparent rod/wood contact. The back faces of the front scan and older simplified envelopes are not a reconstruction of the real rear installation. No drilling/cutting remedy, numeric dimension, or CAD change follows from the photographs. Rebuild with `./project prepare-rear`; the original CB01 and earlier scenes remain preserved.

**Current appearance candidates are circular and concentric with each actual cover.** The prior F005 offset/rectangular appearances are historical and do not meet the accepted border requirement. R005 remains the accepted plate/foam measurement baseline; the six installed center readings are preserved in RECON-001, with a separate fitted diagnostic state. No scan, valve or stud was moved to force fit.

- [Current CB01 illustrated review](deliverables/current/fabrication/concentric-border-study/index.html), served at `http://127.0.0.1:8765/fabrication/concentric-border-study/index.html`.
- C1: main diameter 220 mm / diverter 120 mm; ideal borders 17.925 / 10.7875 mm; conditional gap 5.238 mm.
- C2: main diameter 214.15 mm / diverter 128.425 mm; both borders 15 mm; conditional gap 3.950 mm.
- Worst projected main damage margins are 7.405 / 4.480 mm after the prior trace allowance. Neither proves continuous sound support or satisfies the earlier exploratory 10 mm target. Actual cover registration, scale and supported seal detail remain open.
- [Blueprints](deliverables/current/fabrication/concentric-border-study/concentric_blueprints_CB01_DRAFT.pdf), [1:1 templates](deliverables/current/fabrication/concentric-border-study/full_size_templates_CB01_DRAFT.pdf), [Blender workspace](deliverables/current/fabrication/concentric-border-study/paired_concentric_CB01_DRAFT.blend), and six stock-specific quote ZIPs are in that folder. The 3 mm prototype is not thickness-matched to either 1.524 or 3.175 mm metal option.
- [LOC01 upper locating-tab study](deliverables/current/fabrication/concentric-border-study/stud_locator_analysis.json) compares a round hole and slot at fitted stud positions with unchanged captured surfaces. It has conditional insertion/seated conflicts and unverified bearing/depth. Its diagnostic STEP/STL is excluded from quote packages. Threaded engagement is unselected.
- [Controlling locating requirements](canon/stud_locator_study.json) supplement [constant-border requirements](canon/concentric_border_requirement.json). The lower companion stays circular with its ordinary aperture.

Run `./project prepare-concentric` to rebuild stale stages. It preserves modified deliverables and does not overwrite accepted measurements. Final release still requires real foam tracing, actual stud/cover fit, repeatable concentric placement, support/sealing review and a thickness-correct physical dry fit. No physical test, vendor upload, order or manufacturing release has occurred.

## F005 - historical fabrication preparation

**2026-10-15 design correction:** The user rejects unequal exposed borders. Each backing plate must be concentric with its actual circular Kohler cover and show constant border width all the way around. F005's offset main plates and rounded rectangular alternatives do not satisfy this requirement. Read [the accepted requirement](canon/concentric_border_requirement.json), [the separate concentric draft comparison](deliverables/current/fabrication/concentric-border-study/index.html), and [where the top gouges sit beneath the exposed border](deliverables/current/fabrication/concentric-border-study/damage.html). F005 files below remain a historical preparation package, not an accepted appearance.

**Two complete custom plate pairs are prepared for prototype and quote review. Permanent manufacture remains on hold for the actual foam trace, hardware/cover fit, support and explicit release.** Accepted measurement evidence is now **R005**; **F005** remains the design revision because the two confirmed edge contacts match its prior trial geometry. The 46.25 mm gap is between inside opening edges; 35.23 mm runs from the lower opening bottom inside edge to the bottommost outside rim. The lower bore and rear cavity remain unmeasured.

- [Current illustrated design review](deliverables/current/fabrication/F005/index.html), served at `http://127.0.0.1:8765/fabrication/F005/index.html` by the existing local review server.
- [Consolidated comprehensive goal prompt](docs/fabrication_goal_prompt.md), retaining the original complete scope and prioritizing this immediate preparation.
- [Eight-sheet blueprint/specification PDF](deliverables/current/fabrication/F005/blueprint_specifications_F005_DRAFT.pdf).
- [Fit and fabrication research PDF](deliverables/current/fabrication/F005/fit_and_fabrication_report_F005_DRAFT.pdf).
- [Full-size templates](deliverables/current/fabrication/F005/full_size_templates_F005_DRAFT.pdf): A3, 100% printing, two 100 mm calibration bars.
- [Paired Blender workspace](deliverables/current/fabrication/F005/paired_escutcheons_F005_DRAFT.blend): both cosmetic variants, unchanged observed source, measured reference plates and exploded order. Official Kohler exterior meshes replace generic handles. Cosmetic views explicitly hide captured hardware; they do not show a proven fit.
- [Design canon](canon/fabrication_designs.json), [public vendor research](canon/fabrication_research.json), [computed results](deliverables/current/fabrication/F005/analysis.json), [triangle insertion check](deliverables/current/fabrication/F005/mesh_path_check.json).
- Six `quote_package_{A|B}_{SS060|SS125|PROTO3}_F005_DRAFT.zip` files in the F005 folder. Choose one pair and one thickness. Each contains only that pair's custom CAD, selected drawing sheets, notes and hashes; no source scan or homeowner photos. Nothing has been uploaded or ordered.

Validation: [F005 executed checks and remaining gates](docs/validation/fabrication_F005.json). Prior accepted readings are preserved, two contact-defined gaps are added, and the saved original full scan/proxy geometry is unchanged. All custom exports pass; this is not a physical fit or manufacturing release.

A uses a 230 mm circular main plate offset 6 mm upward and a 120 mm diverter companion, with a conditional 6.24 mm gap. B uses a 220 x 218 R62 main and 120 x 120 R35 diverter, with an 11.24 mm gap. The shaped main aperture clears the modeled forward insertion sweep, but its clearance to the real rear foam path is not established. Actual caliper readings are not changed to force fit. Conditional measured mounting centers (112.05 mm if both holes are 5.66 mm) disagree with captured tip centers (108.01 mm). Unchanged stud depths also conflict with the cover cavity assumption. Neither discrepancy authorizes cutting, wood drilling or valve relocation.

Next physical step: trace both rear foam edges on the template; remeasure studs as planned; dry-fit a thickness-correct prototype with real factory parts and check support, seating, operation, drainage and removal. Finalize material/finish and qualified seal/support detail, then record release against the correct revision. Vendor costs are unquoted planning allowances; published production times are distinct from delivery dates.

```sh
./project prepare-fabrication
./project validate --git-objects
./project handoff
```

`prepare-fabrication` reads canon and reuses unchanged stages. It refuses a mismatched evidence revision. Preserve any manually changed generated file before rebuilding; the normal manifest backup mechanism applies. Reconcile new measurements rather than silently migrating a fabrication design.

---

## Supplemental installed-center reconciliation — 2026-10-15

Six newly reported center distances and the user's permission to smooth their imperfect caliper readings against the weaker primary scan are preserved in [the evidence record](docs/physical_checks/installed_center_distances_2026-10-15.json). See [the readable reconciliation](deliverables/current/analysis/center_reconciliation_DRAFT.txt) and [numeric sensitivity study](deliverables/current/analysis/center_reconciliation_DRAFT.json); rerun with `./project query reconcile-centers`. The user now confirms these are straight-line 3D distances between end-tip centers at unequal depths. RECON-001 revision 2 preserves every number, compares like-for-like 3D lengths, and shows conditional wall-plane reductions of 0.013–0.423 mm using the current scan depths. All six lengths admit an exact free-depth 3D arrangement; its orientation/depth relative to the wall remains unknown. Planar trials are retained only as counterfactual sensitivity checks. Fixed-depth fits and both free-depth mirror branches remain separate from raw evidence. Measurement uncertainty, assembly clearance, machining tolerance and sealing/support requirements are distinct. It is a supplemental DRAFT: no derived dimensions have been selected for the R005/F005 CAD baseline, and fit residuals are not accuracy bounds. Actual stud diameters, axes at the plate plane, and physical fit remain unverified.

## R005 measurement update

The current measurement review and Blender baseline use R005. New readings should use R005; the R004 instructions below are a preserved historical checkpoint. See [the endpoint clarification record](docs/physical_checks/outer_plate_contacts_2026-10-15.json). Exact center spacing and cover registration remain unresolved until the lower bore is measured.

- [Current measurement review](deliverables/current/review/index.html)
- [Current baseline Blender workspace](deliverables/current/blender/installation_R005_DRAFT.blend)
- [Current worksheet](deliverables/current/drawings/measurement_worksheet_R005.pdf)

## Preserved R004 diagnostic checkpoint (historical reference)

### Measured outer-cover update — R004

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
