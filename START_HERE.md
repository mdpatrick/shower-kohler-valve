# Shower escutcheon project — FT02 / R006

**The two custom plate designs are prepared for a quote and sacrificial physical fit trial.** Private Ponoko quotes have been obtained. No purchase, physical fit, permanent installation or water test has occurred. Open the [current illustrated handoff](deliverables/current/fabrication/FT02/index.html), or run `./project review`.

**Friend's 3D print: RF03.** [Download the clean print package](deliverables/current/fabrication/FT02/formwork-print/RF03_FRIEND_PRINT_PACKAGE.zip) or [open its illustrated guide](deliverables/current/fabrication/FT02/formwork-print/index.html). Print ONE temporary form, normally the continuous 12 mm collar; the relieved 24 mm collar is an optional alternative. The panel is reduced from 12 to 8 mm, with the same 2 mm collar wall and smaller 12 × 8 mm locating slots. PETG, 5 walls, 1.2 mm skins and 25% infill; 240 mm diameter needs 250 × 250 mm usable bed area including brim. The ZIP has isolated, pre-oriented STL/geometry-only 3MF and STEP files, a three-page PDF and settings. Budget $75 as a generous hobby-print payment including one retry; actual slicer time is unknown. Independent padded bracing and physical seating/release checks remain required. All formwork is removed; this is separate from the final escutcheon plates. Rebuild: `./project prepare-form-print --stage cad|capture|render|documents|audit` in that order. See `canon/formwork_print_RF03.json`.

**Finish comparison:** [FIN01 stainless beside Kohler brushed nickel](deliverables/current/fabrication/FT02/finish-study/index.html) shows three CAD appearance views on the captured travertine and actual reference photos. The colors are illustrative; a physical sample is needed to judge a close finish match. Rebuild with `./project preview-finishes`.

**Latest October 17 refinement:** [TR03 / RF02: smaller slots, tabbed form and deeper-collar options](deliverables/current/fabrication/FT02/tab-refinement/index.html). Owner confirms removable rod-end nut. New 12 × 8 mm flat slots replace TR02's 18 × 10 mm study size; current FT02 order files remain intact. RF02 adds front locating tabs to the temporary form: 12 mm continuous collar, or 24 mm maximum skirt with rear reliefs and only 12 mm continuous molding wall. The simple deeper full collars conflict with captured surfaces. Permanent retained-collar use is not established. See `canon/tab_refinement_study.json` and `docs/physical_checks/removable_trim_nut_2026-10-17.json`.

**Earlier October 17 explanation:** [TR02 narrated video: tabs, smaller opening, both scans, handles and RF01 formwork](deliverables/current/fabrication/FT02/tab-rethink/index.html). Adding inward tabs does not move the foam. TR02 tests loose locating slots and 1–2 mm more inward backing while preserving Ø220. Its CAD and video remain historical studies.

## Order one pair in one material

The selected main plate is Ø220 mm with one centered upright capsule opening, 116.35 × 151.10 mm, R58.175 ends. The selected diverter ring is Ø124 / Ø80 mm. Each manufacturing STEP contains one custom plate solid, centered at X=Y=0, back Z=0, front Z=stock thickness, in millimeters. No wall or factory hardware is included.

The selected FT02 main has **no permanent bolt tabs**. Its earlier R006 round-hole/slot candidates introduced captured-shaft interference and uncertain registration between the formed inner plate and new flat sheet. The later TR02 study extends the tabs and slots inward and adds backing around the opening. Loose slots allow adjustment; they do not themselves move the foam or cause a leak. Visually align the backing and then retain its position with a suitable support/seal detail. For the selected no-tab files, use the removable front border gauge on the real factory cover; it is not left beneath the gasket.

| Alternative route — quantity one main + one diverter | Quoted total, USD | Ordinary timing observed 2026-10-16 | Finish limitation |
|---|---:|---|---|
| **Recommended first: clear acrylic, 1.50 mm** | **$43.79** | 3 business-day production; UPS Ground; estimated October 26 | Dry-fit/contact inspection only; handle gently |
| #4 brushed 304 stainless, 1.52 mm | $80.47 | Same displayed production and arrival | Main includes Linear Deburring; diverter is As cut and needs safe-edge finishing arranged |

Totals include the displayed $16.16 delivery; tax was not separately shown. Extra metal finishing is unquoted. Metal is about 1.84× clear before that work. Clear-first makes gasket contact and interference easier to inspect. Metal-first is reasonable if the additional finishing is arranged and possible remake cost is acceptable. Recheck totals/arrival before purchase. Neither quote guarantees a Kohler brushed-nickel match, flatness, physical fit or sealing.

- [Clear route ZIP](deliverables/current/fabrication/FT02/FT02_CLEAR_FIT_TRIAL.zip) · [exact two-file upload list](deliverables/current/fabrication/FT02/CLEAR_FIT_TRIAL/UPLOAD_LIST.txt).
- [Metal route ZIP](deliverables/current/fabrication/FT02/FT02_METAL_FIT_TRIAL.zip) · [exact two-file upload list](deliverables/current/fabrication/FT02/METAL_FIT_TRIAL/UPLOAD_LIST.txt).
- [One-page owner instructions](deliverables/current/fabrication/FT02/ORDER_AND_NEXT_STEP.pdf) · [dated quote record](deliverables/current/fabrication/FT02/ponoko/quotes.json) · [unsent finishing questions](deliverables/current/fabrication/FT02/ponoko/QUESTIONS_FOR_FINISHER_DRAFT.txt).

Upload one DXF per physical part. STEP/STL are alternate representations, not extra items. Acrylic `PONOKO_K020_CUT` files contain the documented 0.20 mm kerf compensation; their path outer diameters are 220.20 and 124.20 mm, targeting finished 220 and 124 mm. Metal DXFs use finished profiles; Ponoko compensates them. Do not compensate twice. Each route ZIP has shop drawings, isolated previews and hashes.

Ponoko uses one mutable cart, ID 1268443. Its contents have changed during quote comparisons; consult the dated quote record and inspect the cart before ordering. Separate private formal exports preserve both material alternatives under `build/FT02/ponoko_private/`. Do not combine both pairs. Account/session and destination details are excluded from Git. Only custom part DXFs were uploaded, not scans, photos or the installation assembly. No staff message or order was sent.

## Bring these to the installer

- [PLUMBER_START_HERE.pdf](deliverables/current/fabrication/FT02/PLUMBER_START_HERE.pdf): three pages with actual front/rear photos, factory sequence, depth branches, support/seal checks and a pre-visit message draft.
- [Installation guide](deliverables/current/fabrication/FT02/INSTALLATION_GUIDE.html) and [PDF](deliverables/current/fabrication/FT02/INSTALLATION_GUIDE.pdf): incoming inspection through protected trial, conditional repairs, sealing/cure, function, drainage, water checks and service.
- [Tiled Letter cutting template](deliverables/current/fabrication/FT02/TEMPLATES_LETTER.pdf), [separate reference overlays](deliverables/current/fabrication/FT02/REFERENCE_OVERLAYS_LETTER.pdf), and [A3 version](deliverables/current/fabrication/FT02/TEMPLATES_A3.pdf). Print at 100%; measure both scale bars. Paper checks XY, not depth or sealing.
- [Engineering record](deliverables/current/fabrication/FT02/ENGINEERING_RECORD.pdf), [CAD/capture checks](deliverables/current/fabrication/FT02/engineering/locator_evaluation.json), [fresh export audit](deliverables/current/fabrication/FT02/audit.json), and [fresh adversarial/visual review](docs/validation/adversarial_review_FT02.json).
- [Portable three-scene Blender file](deliverables/current/fabrication/FT02/escutcheon_fit_trial_FT02.blend): actual attached scan, proposed pair on travertine, and exploded reference assembly. Factory reconstructions are visual references, not manufactured replacements.

The expert assembles/installs; no new CAD survey is assigned. First establish correct factory adapters and handle engagement. If only trim rods are too long because their backs touch wood, conditional wood relief is the owner's preferred remedy. If the valve/handle depth is wrong too, resolve that before assembly or casting. No additional tile cutting, grinding, drilling, enlargement or retiling is authorized.

Ordinary physical checks remain: both plates clear the actual hardware and each other; full factory gasket/contact lands; the plates stay flat, supported and centered; correct nuts/covers/hubs seat without force; controls operate and remain removable; intended bottom drainage is retained. Then document the compatible repair/seal system, its cure and separate plumbing-pressure and shower-spray checks. Free foam depth and a generic 5 mm allowance do not establish engagement or watertightness.

## Optional repair form — not an extra plate to order

**Trial the plates first.** If the installer finds sound, stable bearing support, omit RF01. If missing support requires a small supported perimeter repair, the separate [RF01 tool package](deliverables/current/fabrication/FT02/RF01_REPAIR_FORM_TRIAL.zip) contains one PETG forming face/collar, print STL, STEP, specification, bill of materials and checks. Read [setup/removal instructions](deliverables/current/fabrication/FT02/REPAIR_FORM_SETUP.pdf) and [drawing](deliverables/current/fabrication/FT02/REPAIR_FORM_DRAWING.pdf) before making it.

RF01 is temporary: stabilize from the shower side, protect hardware, fill only the specified supported zones from the rear, allow the selected material to develop appropriate strength, and withdraw the tool toward the shower. Remove every film/pad/tool piece. Its collar clears the tested captured scope, but full face seating, stable supports, release and service access still require a physical rehearsal. The form is not a permanent waterproof liner and is not part of either Ponoko order. No form quote was obtained; its projecting collar cannot be made by ordinary flat laser cutting. It does not change the selected plate geometry.

## Final accepted planar measurements

Loose inner plate, front toward handles. LEFT/TOP reference contacts define x right/y down. FX/FY readings reach the **far inside hole wall**, not the center. These are user-confirmed coplanar caliper observations; hundredths displayed do not certify instrument uncertainty.

| ID | Accepted mm | Meaning |
|---|---:|---|
| DA / DB | 5.66 / 5.66 | Upper-right A / lower-left B bore diameters |
| FAX | 119.17 | LEFT to A far/right wall; supersedes 118.79 |
| FBX | 16.38 | LEFT to B far/right wall |
| FAY | 61.40 | TOP to A far/bottom wall |
| FBY | 108.85 | TOP to B far/bottom wall; supersedes 109.06 |

Derived centers: A=(116.34,58.57), B=(13.55,106.02) mm, y down. Center distance 113.2135 mm; predicted nearest-edge diagonal gap 107.5535 mm. Preserve the older 106.39 mm gap separately; it was not averaged into this layout. See [R006 import](canon/measurement_responses/R006.json) and `canon/measurements.json`.

Installed stem/stud **tip-to-tip distances are 3D**, with endpoints at different depths; they are not planar hole coordinates. The original installed scan/transform remains unchanged. Secondary reflective scans and the attached-inner-plate scan remain separate evidence. Its apparent stem offset is not corrected away or treated as precise machining evidence. [Attached scan assessment](deliverables/current/fabrication/fit-trial/attached_scan_assessment.json).

Use supported reconciliation and forgiving geometry before requesting another owner reading. A new request must change an indispensable machining decision and explain exact illustrated contacts, plane, method and needed precision. No additional owner measurement is requested for this release. Long historical field forms remain optional.

## Rebuild and preserve

`canon/fit_trial_design.json` governs selected geometry; `canon/fit_trial_handoff.json` holds editable prose. `canon/repair_form_design.json` governs RF01. Use `./project prepare-fit-trial` or `--stage analysis|blender|documents|audit`. Blender background processing requires the documented desktop permission on this Mac. Preserve annotations separately. Generated checks are software evidence; they must never mark physical checks complete.

Reproduce the separate narrated study with `./project rethink-tabs --stage analysis|speech|render|preview|encode|verify` (or `all`). Local macOS speech synthesis and Blender background rendering require desktop access; the sandbox can return empty speech. The builder rejects empty audio. RF01's original tool geometry is read without alteration.

`./project query solid MAIN`, `solid DIV T1500`, `dimension main.outer_diameter_mm`, `coverage CUT-03`, `clearance`, `depth`, and `compare-states` use the current selected design. `./project query historical ...` is explicitly older reconstruction. `./project validate --git-objects` verifies preserved source bytes and the current manifest. `./project handoff` creates a private local Git bundle and review ZIP; neither is an off-machine backup.

FT01, F005, CB01, AP01 and GP05 remain history. Do not send their variants or whole-shower STEP assemblies as current plate orders. No Pro response was received or required for this delivery. [Previous starting page](docs/decisions/history/START_HERE_pre_FT02.md) · [current delivery goal and narrow Ponoko authorization](docs/decisions/delivery_goal_with_ponoko_2026-10-16.md) · [original request](docs/project_request.md).
