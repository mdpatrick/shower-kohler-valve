Continue the EXISTING local project at \`\~/Code/shower-kohler-valve\`. This is a delivery run, not a new reverse-engineering project. Use the accepted measurements below, finish the necessary design decisions, and produce the smallest justified set of custom plates that the owner can order and bring to a Kohler plumber.\
\
Inspect the live repository and compare it with the available GP05 review before modifying designs or exports. Work from the verified project state.\
\
The next outcome is a fabrication-ready \*\*fit-trial release\*\*: internally consistent plate-only files with no known disqualifying geometry, an intelligible ordering choice, and installation instructions. Actual fit, support, sealing and water performance require subsequent physical checks. Do not conflate those checks with a reason to withhold useful trial files.\
\
Evaluate a CAD-defined removable plastic repair form: a temporary front forming face with a collar projecting into the wall opening, allowing a contractor working from the rear/closet to rebuild the missing wall perimeter while preserving the valve's clearance and service space. Deliver the tool separately when viable. Distinguish it from the clear acrylic fit-trial escutcheon and from a permanent plastic liner.\
\
\## 1. Preserve working project infrastructure and actual evidence\
\
Inspect \`AGENTS.md\`, current goals, Git status, existing work and revisions. Reuse the working CAD, Blender, analysis and document-generation pipeline. Make scoped commits, protect unrelated changes, preserve original observations and record design decisions. Do not reinitialize Git, reinstall working tools, migrate storage, rewrite history or unnecessarily reorganize the project. GP05 records the source archives as ordinary Git blobs; leave that alone unless the live repository establishes otherwise.\
\
GP05 reference snapshot: source baseline \`fbe55d6475383feca03e9f337fbf6f450f336c89\`, measurements R005, design FT01. Verify these against the live repository and allocate the next unused measurement and design revisions.\
\
Start with the existing canon, design/handoff records, physical-check records, source transforms, actual CAD exports, GP05 addenda and independent review when available. Relevant existing paths include:\
\
\- \`canon/measurements.json\`, \`canon/fit_trial_design.json\`, \`canon/fit_trial_handoff.json\`.\
\- \`docs/physical_checks/\` and applicable manufacturer evidence.\
\- \`deliverables/current/fabrication/fit-trial/\` and its reports.\
\- \`src/fabrication/fit_trial.py\`, \`fit_trial_documents.py\`, \`audit_fit_trial.py\`, and \`src/blender/fit_trial.py\`.\
\- Existing \`./project prepare-fit-trial --stage analysis|blender|documents|audit\` and \`./project validate --git-objects\` commands, where still current.\
\
\*\*Original Polycam photogrammetry exports:\*\*\
\
\`\`\`text\
\~/Downloads/shower-hole-valve-polycam.zip\
\~/Downloads/plates-side-1-polycam.zip\
\~/Downloads/plates-side-2-polycam.zip\
\`\`\`\
\
Prefer intact repository copies when their recorded hashes match these originals. If a required archive is absent from the repository, copy it from the specified Downloads path into the existing source-asset structure, preserving its bytes and verifying a SHA-256 hash. Do not move/delete the Downloads originals, rename files inside an OBJ/material/texture package, replace conflicting captures silently, or duplicate large archives unnecessarily. Resolve differences by inspecting provenance. Keep derived extraction/processing separate from source evidence and make delivered assets independent of Downloads. Preserve the live repository's existing storage strategy; these paths do not authorize a new Git/LFS migration or external upload. If a local path is genuinely missing, report the exact one after attempting access and continue from intact available evidence.\
\
The strongest installed scan is \`shower-hole-valve-polycam.zip\`. The reflective \`plates-side-1-polycam.zip\` and \`plates-side-2-polycam.zip\` are secondary references. An attached-inner-plate capture can help with pose and visible interfaces but cannot independently validate a dimension used to scale that same capture. Preserve real damage, misalignment and surface topography; do not edit the observed installation to make a proposal fit.\
\
Use accepted dimensions for the measured physical features, credible scan regions for installed context, and applicable Kohler documents for factory requirements. Generated images are not dimensional or hardware evidence. The inner plate has \*\*TWO small mounting holes, upper-right and lower-left\*\*. Its two large openings are for the controls.\
\
Identified products:\
\
\| Component | Model |\
\|---|---|\
\| Main Purist stacked trim | K-T14489-4-BN |\
\| Main thermostatic/volume valve | K-2973-KS-NA |\
\| Separate Purist diverter trim | K-T14491-4-BN |\
\| Separate diverter valve | K-737-K-NA |\
\
Match the actual hardware revision before applying instructions. Do not assume planned copper replacement or valve relocation has already happened; note any changes since the captures.\
\
No further tile cutting, grinding, drilling or retiling is authorized. Supported local repairs and suitable custom plates remain candidates. Retain the intended factory sealing, trim and service components. No external scan/CAD upload, paid API use, vendor contact, remote push or order is authorized by this goal; prepare the files and draft communications locally.\
\
\## 2. Import the accepted measurements as the active locating-layout inputs\
\
Use the following accepted loose-inner-plate caliper readings. Do not request repeat measurements by default or average these values with superseded readings.\
\
\*\*Measurement frame:\*\* loose inner plate viewed from the front, facing the shower handles. TOP and LEFT reference-block contact faces define y=0 and x=0. x increases rightward; y increases downward. A is the upper-right small mounting hole; B is the lower-left small mounting hole. FX/FY readings end at the FAR inside wall of the relevant hole, not its center.\
\
\| ID | Meaning | Final accepted reading, mm |\
\|---|---|---:|\
\| DA | Hole A diameter | 5.66 |\
\| DB | Hole B diameter | 5.66 |\
\| FAX | LEFT reference to A's far/right inside wall | 119.17 |\
\| FBX | LEFT reference to B's far/right inside wall | 16.38 |\
\| FAY | TOP reference to A's far/bottom inside wall | 61.40 |\
\| FBY | TOP reference to B's far/bottom inside wall | \*\*108.85\*\* |\
\
\*\*Canon update:\*\* FAX=119.17 mm supersedes 118.79 mm; FBY=108.85 mm supersedes 109.06 mm. Both hole diameters are confirmed as 5.66 mm. Preserve superseded observations in the evidence record, not as active dimensions. Repeated readings do not establish a certified instrument uncertainty; do not infer ±0.01 mm accuracy from display precision.\
\
Compute centers from the actual contact method, not by fitting to a desired result:\
\
&#x20;   radius_A = radius_B = 2.83 mm\
&#x20;   A = (119.17 - 2.83, 61.40 - 2.83) = (116.34, 58.57) mm\
&#x20;   B = ( 16.38 - 2.83,108.85 - 2.83) = ( 13.55,106.02) mm\
\
These are coordinates from LEFT/TOP, y DOWN. Checks derived from those inputs are:\
\
&#x20;   horizontal separation = 102.79 mm\
&#x20;   vertical separation   = 47.45 mm\
&#x20;   center distance       = sqrt(102.79^2 + 47.45^2) = 113.2134559... mm\
&#x20;   predicted nearest-edge diagonal gap = 113.2134559... - 5.66\
&#x20;                                       \= 107.5534559... mm\
\
For comparison ONLY, using the recorded outer outline W=130.35 mm and H=165.10 mm, an outline-centered frame with +Y UP gives:\
\
&#x20;   A = (+51.165, +23.980) mm\
&#x20;   B = (-51.625, -23.470) mm\
\
The hole midpoint is (-0.230,+0.255) mm from that nominal outline center. Do not force symmetry or move both holes onto a mathematically prettier pattern. Height was tape-measured; these derived decimals do not improve its accuracy.\
\
\*\*Do not directly equate these outline-centered coordinates with the new backing plate's coordinates.\*\* Establish the transform from the measured inner plate to the actual outer decorative trim and its installed pose. The custom outside profile is centered on that decorative trim, not automatically on the hole midpoint, opening midpoint or inner outline midpoint. Record the rigid transform, front/back orientation and any remaining approximation.\
\
The recorded 106.39 mm nearest-edge diagonal gap implies 112.05 mm between centers with two 5.66 mm holes. This differs from the accepted coordinate survey by approximately 1.16 mm. Retain the discrepancy in the evidence log, but \*\*construct the active layout from the accepted coordinate survey\*\*. Do not blend incompatible dimensions, fit the layout to the conflicting diagonal, or require another diagonal reading as a default pre-release gate. Assess the discrepancy as a robustness scenario where relevant, not a certified ±1.16 mm error bound.\
\
Record the accepted readings and their provenance, update measurement statuses and dependencies, and rebuild from the active canon. These are loose-plate planar observations. Do not apply a depth correction intended for installed valve-tip measurements.\
\
\## 3. Evaluate bolt-based positioning\
\
Provide reproducible positioning of the repair plate on the wall. Evaluate a simple stud-guided design and prefer it when it improves positioning without compromising fit or sealing.\
\
With the starting capsule and the nominal centered mapping above, both hole centers and their 5.66 mm bores fall inside the access opening. Approximately 6.2–6.6 mm separates the centers from that opening's nearest boundary. They cannot be created by drilling the existing plain plate. A viable locator requires \*\*in-plane material extending inward\*\*, or a revised access profile. Recompute this in the actual registered geometry.\
\
Start by evaluating two minimally intrusive, rounded-root tabs with one round clearance hole and one short closed slot. The slot's long axis should follow the line joining the two nominal mounting locations if its purpose is to accommodate their spacing variation. Choose which end gets the round hole based on access and surrounding geometry. This is a candidate, not a foregone requirement. Two round clearance holes are acceptable if the complete allowance calculation shows they are sufficiently forgiving. Do not default to long arbitrary vertical slots.\
\
These are \*\*clearance/locating features around existing studs\*\*, not new tapped attachments to the valve or permission to add wall screws. The measured 5.66 mm factory-hole diameter is not automatically the custom-hole diameter and is not the rod's diameter. Inspect the actual stud/thread envelope, factory hole clearance and relevant offsets. Do not use a thread-root diameter where the thread crests must pass. Do not purchase precision locator hardware merely to imitate a tooling-fixture example.\
\
For the selected concept, explicitly check:\
\
1\. The relation between the loose plate's measured hole plane and the proposed tab plane, including formed-plate depth, gasket/bedding stand-off, stud angle, and sheet thickness. Copying XY locations across different Z planes is an approximation unless the axes justify it.\
2\. Tab, slot and ligament clearance to the valve casting, diagonal mounting bracket, nuts, bosses, inner-plate back surface, and original service openings. Retain useful access and the actual assembly/removal path. Never use an added tab as an accidental rear stop that prevents gasket seating.\
3\. Sufficient tab width, remaining material and rounded transitions for the selected material/process. Acrylic needs its own fragility/handling assessment; it is not steel with a different color. No mandatory permanent bending, brittle snap-off tabs or forced fitting.\
4\. The allowance budget: stud envelope, incoming cut accuracy, observed disagreement, plane/pose uncertainty and plausible installation variation. Specify chosen hole diameters, slot width/length/orientation and their basis. A slot accommodates variation along its length, not arbitrary transverse error.\
5\. Residual freedom of the whole stack, including clearance in the factory inner-plate holes. Demonstrate resulting centering error, rotation, gasket support and worst-gouge coverage across the allowed movement. Two oversized features do not guarantee perfect centering; perfect nominal hole coordinates do not eliminate assembly play.\
6\. Retention in Z and the load path. Studs passing through clearance holes do not automatically clamp the backing plate. Show what keeps it flat and prevents shifting during and after assembly without changing intended factory engagement or forcing the plate into the void.\
7\. An uninterrupted factory gasket landing and an effective new plate-to-wall sealing path, with drainage/service implications of every added opening.\
\
Use current local evidence, targeted calculations and a practical trial. Do not restart the scan reconstruction or require another general hole survey. Evaluate the actual candidate geometry; the archived LOC01 interference result applies only to its tested design.\
\
\*\*Decide and deliver:\*\* select one main-plate profile, not a menu of experiments. Prefer the simple locating version if no known disqualifying conflict defeats it and remaining fit uncertainty is reasonably testable. If safe, useful locating features cannot be justified from the current data, deliver the plain profile with a removable concentric positioning aid and a short illustrated explanation of the specific conflict or tradeoff. Base the locator decision on verified geometry and installation requirements. Keep the fallback in source/history, out of the active purchase folder.\
\
Final installation can use the real cover or a nonmarring removable jig to take up small remaining play. Such an aid is not a permanent spacer under the gasket and must be removable without displacing the plate or contaminating sealing surfaces.\
\
\## 4. Keep the plate set and machining scope simple\
\
Retain these default envelopes unless a specific check justifies a change:\
\
\| Part | Starting XY geometry | Metal thickness |\
\|---|---|---:|\
\| Main | OD 220.00 mm; upright capsule 116.35 mm wide × 151.10 mm overall high, modified locally only as justified above | 1.524 mm |\
\| Diverter | OD 124.00 mm; concentric opening 80.00 mm | 1.524 mm |\
\
The unmodified main capsule has R58.175 mm ends, centers y=±17.375 mm and a 34.75 mm straight section. Adding tabs changes the profile, area, contour count and any analytic-volume checks; do not keep claiming the finished part has an unobstructed capsule. The 80 mm diverter opening is a trial nominal, not a measured gasket diameter.\
\
Use flat sheet fabrication where possible. No unnecessary milling, countersinks, tapped holes, exotic alloy or decorative complexity. Compare appropriate stainless choices and delivered cosmetic finish without silently changing thickness. Exposed edges need safe, finished treatment; decorative-face condition and grain direction require actual supplier agreement, not the word “deburred.” Do not promise an exact Kohler BN match.\
\
Provide one metal route and, only as an alternative purchasing route, a clear dry-fit version as close as practical to 1.524 mm. Verify approximately 1.6 mm clear acrylic availability in the current supplier catalog or quote. Use supplier-confirmed nominal thickness in each STEP/drawing, measure the received part, and state the difference from the metal stack. Do not use a 3 mm prototype as an equivalent depth trial. A thickness-matched plastic print is a fallback if thin acrylic is unsuitable or uneconomic.\
\
Prefer the same XY design for material alternatives. If safe acrylic tabs require an XY change, either qualify a common profile or label that prototype's limits explicitly; never pass off different locating geometry as validation of the final metal geometry. Do not pay for acrylic that cannot answer the deciding fit question.\
\
Compare available delivered pair costs and lead times. A direct metal trial can be preferable when the cost difference is modest and the finish is suitable. Report actual quotes only when obtained through authorized means; do not upload the CAD for a quote without permission. Missing quotes must not block the release or plumber documents. The owner selects ONE route; default quantities are ONE main plus ONE diverter, not every format or alternative.\
\
Keep the 120/80 diverter dormant. Use it only if the 124 mm version actually conflicts and the reduced coverage/contact remains acceptable. It gains 2 mm of separation and loses 2 mm of radial coverage. Do not order both, overlap the plates or shift a cover off-center to disguise a conflict. Release the main independently if only the diverter remains unjustified.\
\
\## 5. Finish the few checks that can change the machining\
\
Update the measured inner-plate model and its reference placement first. Then check the selected custom profiles against the actual local assets. Correct gaps in the existing checks without rebuilding the project.\
\
\*\*Gasket contact versus access.\*\* Under the existing edge-flush foam model, the capsule nominally supports the approximately 6 mm gasket width plus about 1 mm of inward reserve. It does not provide only 1 mm of total gasket support. Actual backside shape, contact variation and pose still matter. Preserve the full needed contact path; do not globally enlarge the opening for clearance or shrink it for gasket support without checking both consequences. Prefer a justified local adjustment where it solves a real conflict. New locator play must be included.\
\
\*\*Scope of prior clearance checks.\*\* The GP05 \`clipped_capture()\` test used Z≥0.5 mm and an opening mask eroded by 3 mm. Its reported approximately 1.6–2.3 mm clearances do not include every low/boundary feature or prove insertion. Inspect low hardware, brackets, stone boundaries, tab envelopes, factory back surfaces and the actual approach/removal sequence at the proposed thickness and stand-off. Separate intentional support contact from rigid interference.\
\
\*\*Coverage and neighboring plate.\*\* Recompute the worst margin for each gouge and opening edge about the actual cover center, not an idealized hole center. Report sound support/seal overlap separately from visual coverage. The GP05 220/124 scenarios show roughly 3–5 mm between plates; treat those as scenario results, not a guaranteed gap. Check plate position, locator play and any proposed valve movement together. Retain 220 mm unless there is a clear reason to change it. Generate all illustrations from the selected dimensions.\
\
\*\*Diverter.\*\* Check the applicable rear factory plate/contact footprint and assembly path. An 80 mm aperture fitting beneath the decorative cover is not proof of rear seal support. Correct any known conflict before releasing that part; ordinary unverified fit checks belong in the physical trial instructions.\
\
\*\*Form/repair coupling.\*\* If section 8 selects form-assisted rebuilding, include the as-cast opening, finished repair face, any finishing/waterproofing thickness, and removal path in these same checks. The mold's concrete-contact envelope is not automatically the custom plate's aperture. Confirm that the permanent plate still installs after the repair and that the repair does not consume the factory assembly's rear clearance.\
\
Use current canon and justified working nominals. Label assumptions and sensitivity results honestly; no invented confidence percentages or blanket scan-error certificates. Do not overwrite observed damage or physical measurements to get a pass.\
\
\*\*No new numerical measurement request is expected in this run.\*\* Use the accepted data, a forgiving design and the intended fit trial. Only ask for an indispensable missing value if every reasonable safe machining path is blocked and a specific answer changes a particular feature. First rule out a simpler design or independent main-only release. Ordinary fitting, support assessment and plumber adjustments are not a new CAD survey or a pre-order questionnaire.\
\
\## 6. Prepare the plumber to solve the real installation, not redesign the CAD\
\
Make an illustrated diagnostic sequence that keeps three issues separate:\
\
\*\*A. Trim studs.\*\* The owner has confirmed rear contact with wood. Verify actual stud identity, allowable projection and the original datum from the applicable Kohler guide. The reviewed guide specifies a 7/16-inch maximum projection and adjustment if the inner assembly does not seat; do not extrapolate an unexamined new datum or apply that number to a control stem. A stud's overall length is a different dimension. Show the nuts behind the outer cover, not through its unperforated face.\
\
If wood prevents adjustment, have the plumber inspect the member and nearby services, preserve required thread engagement and choose an appropriate remedy. Do not prescribe blind drilling depth, automatic rod cutting, inappropriate replacement screws or tile alteration. Removing or retracting a stud does not move the control shaft.\
\
\*\*B. Handle adapters and cover engagement.\*\* Identify the actual required factory parts and documented adapter/screw options. Incorrect engagement is not proof the valve body must move. Include the correct factory inner plate, gasket, hubs, outer trim and handles. Use a supported diagnostic fit; do not tighten the unsupported inner assembly across the void. Upper main control is volume; lower is thermostatic.\
\
\*\*C. Actual valve depth or alignment.\*\* Only after the appropriate hardware and stud issues are understood, determine whether the valve needs a positional adjustment. Do not prescribe a numeric movement from a reflective scan alone. Added height includes actual sheet and bedding/support stand-off, not merely the nominal thickness. If repositioning is necessary, use the actual two plates/templates to reconfirm coverage, tab alignment, gasket landing and neighbor gap before making the new plumbing position permanent.\
\
The plumber is there to assemble, adjust and test, not produce a research-grade coordinate dataset. If a trial fails, ask for a marked interference location or concise photo, identify whether it is a plate change or ordinary hardware correction, and continue independent safe work.\
\
\## 7. Show a real support, sealing and service detail\
\
Distinguish factory gasket contact, new plate-to-travertine sealing, mechanical support/retention, and concealed wall waterproofing. Pressure-plumbing leakage is another possible water source. A covered cut and a nice render establish none of those automatically.\
\
Provide two practical branches:\
\
\- \*\*Sound support:\*\* the selected metal plate seats stably on appropriate sound surfaces and does not rock or bow under the correct assembly. Complete the defined sealing and factory installation. Do not mandate rebuilding the entire opening without a reason.\
\- \*\*Insufficient support:\*\* identify the particular support/contact regions that need rebuilding. Explicitly evaluate the custom rear-fill form in section 8 as a way to make that repair repeatable. Specify a supported, compatible repair accessible from the existing rear opening where practical. Protect the valve and preserve service access. Do not bridge the cavity with unsupported grout or turn tightening the nuts into a flattening operation.\
\
Use current manufacturer technical data when selecting readily available repair, bonding, waterproofing and sealant products. Document actual substrate preparation, permitted orientation/thickness, necessary backing/primer/reinforcement, curing and water-exposure requirements. Keep mortar, grout, membrane, structural support and sealant roles distinct. No generic skim of coating is proof of concealed membrane continuity; unknown conditions need a small on-site inspection branch.\
\
Draw the new wall-to-plate sealing path separately from the factory bottom drain. Preserve the intended drain without creating an entry path behind the new repair. Show the original gasket's actual landing, all tab/hole penetration implications, how the plate is retained, and how the trim can later be removed. Do not make sealant the assumed structural attachment without evidence.\
\
Define separate plumbing and external-water checks, after required cure, with the rear accessible when practical. The actual manufactured part, correct handles, stable support and functioning drain must be present for final verification. A plastic dry fit does not approve final metal stiffness or water performance.\
\
\## 8. Evaluate and, when useful, deliver a removable wall-repair form\
\
\### Purpose and scope\
\
Evaluate a plastic/acrylic or 3D-printed forming tool with a flat front face and a collar projecting rearward into the damaged opening. A contractor would place suitable repair material from the existing rear/closet access, OUTSIDE the collar, while keeping the valve, stems, fasteners and required access volume INSIDE the protected no-fill region. After appropriate curing and removal, the intended result is a smaller, properly supported opening with a controlled finished face, rather than an unsupported metal bridge or a cosmetic grout smear.\
\
Complete a bounded feasibility assessment using the available evidence. Prioritize the main thermostatic opening; make a diverter form only when its support repair actually warrants one. A form does not have to reproduce the decorative plate's exact outer diameter. Compare a simple assembled front panel plus split collar with a one-piece print; choose the easiest credible tool rather than an elaborate molded assembly.\
\
Use a removable tool as the starting design. A permanently retained liner is a materially different alternative requiring an explicit reason, reviewed material/contact compatibility, durability, support and sealing interfaces, and unobstructed future servicing. Do not silently leave ordinary prototype plastic embedded in the finished shower. Conversely, do not label removability proven until the extraction path has been checked.\
\
\### Define what the form controls\
\
1\. \*\*Position and finished face.\*\* Register the tool to sound existing stone and the accepted trim/valve coordinate system, not to the jagged opening's visual center. Identify actual reference pads/edges, temporary retention, and a checkable XY/Z setup. The WALL-FACING molding face determines the as-cast front surface; the shower-facing face or total plastic thickness is not that datum. Account for removable liners, pads, finish layers and planned waterproofing so the final support face ends at the intended plane. Do not assume existing tile is perfectly flat or equate inner-plate hole centers to the decorative-cover center.\
2\. \*\*Collar/no-fill region.\*\* Derive its exterior concrete-contact shape and depth from the final required opening, valve/hardware envelopes, installation and future service paths, stud adjustments, chosen tabs, and a justified clearance allowance. Protect more than the visible knob stems: preserve cartridge/stop access, fasteners, bracket space and required tooling. Do not blindly reuse the metal plate's 116.35 × 151.10 mm capsule or the plastic plaster guard outline. Its outer surface controls the as-cast hole; its wall thickness and clearance also have to fit around the actual hardware.\
3\. \*\*Specific repair volume.\*\* Show precisely where material is to be placed from behind and where it must not go. Include the necessary front forming face over the missing areas, any side/back closures, and the practical route for placing/compacting and inspecting the fill. Do not imply that a narrow inner collar alone establishes the finished wall plane or contains the patch. No whole-cavity pour, burial of plumbing, or added water to make an unsuitable mortar flow.\
4\. \*\*Temporary versus permanent support.\*\* Show how the form is held during placement without drilling/cutting existing tile or loading/moving control stems, pipes, cartridges, or unsupported trim. Do not assume clearance holes provide clamping or that tape is adequate for the placement load. Separately identify the sound substrate, repair bond or permanent backing that will support the cured material after the tool is gone. Do not count a removable panel as permanent backing or fresh patch material as its own anchor.\
5\. \*\*Release and extraction.\*\* Draw the actual assembly AND removal sequence with the real hardware in place. Use split, separable or otherwise removable pieces when necessary; address undercuts, reentrant tabs/bolt holes, projections, draft direction, joints, and access to tool fasteners. No requirement to pry against travertine, chip out cured repair, unscrew a trapped part, or disturb plumbing merely to remove a poorly designed form. Keep a protective removable cover/no-fill boundary around vulnerable parts during placement; masking alone is not load-bearing protection.\
6\. \*\*Material and finish of the tool.\*\* Select the simplest practical plastic/panel/print construction for temporary use. Check rigidity/deflection under expected placement, dimensional accuracy, seams, alkaline/moisture exposure, curing heat where relevant, and demolding compatibility. The roughly 1.6 mm clear flat-fit plate is not automatically stiff or complete enough for formwork. Separate any validated liner/release system from the stone and surfaces that must bond, receive sealant, or be waterproofed; do not prescribe household oils or release chemicals without checking compatibility and residue removal. Keep layer texture and panel-joint steps off critical finished contact surfaces or specify a validated finishing method.\
7\. \*\*Repair material and water detail.\*\* Select materials from current manufacturer data for this substrate, vertical/rear-access placement, supported thickness and cure conditions. Ordinary grout is not a default structural patch. A useful mold controls geometry; it does not establish repair bond, strength, absence of voids, waterproofing continuity, or a leak-free installation. Specify those independently, including access for preparation/inspection and a practical method to confirm the patch remains bonded/supported after demolding. If a concealed substrate fact changes feasibility, identify the narrow on-site inspection branch instead of inventing wall construction.\
8\. \*\*Final assembly.\*\* Show the finished arrangement explicitly. With the custom plate retained, the intended sequence is repaired/supporting wall → defined wall-to-plate seal → custom metal plate → original gasket/inner plate → original decorative cover. The factory gasket can land on metal supported by rebuilt wall; do not depict the gasket and custom plate occupying the same wall plane. If direct gasket-to-repaired-wall seating eliminates the custom plate, check visible gouge concealment and all interfaces before selecting that alternative. Rebuild only the needed support/contact regions unless more extensive repair has a demonstrated benefit.\
\
\### Contractor sequence and proof\
\
Coordinate final valve position, remaining copper work, tool dry fit, substrate preparation/permanent backing, tool positioning, protected rear-side placement, cure/stripping, surface checks and factory reassembly. Do not cast around a pose that the plumber still intends to change. Distinguish stripping time, readiness for coating/sealant, assembly-loading time, and water exposure; use the selected product instructions rather than one generic “dry time.”\
\
Provide front, rear and section views showing the current opening, form/collar, no-fill region, permanent support, repair volume, surface datum and cured result AFTER the form is removed. Include accessible checks for position, form stability, complete fill/contact, retained clearances, removal, and a flat stable bearing surface. A source-backed method plus physical checks is the objective, not a claim of a guaranteed “perfect” repair.\
\
\### Deliver and keep the project moving\
\
If feasible and worthwhile, export the selected tool as a separate \`REPAIR_FORM_TRIAL\` package: individual CAD STEP parts, print-ready STL/3MF for printed parts, clean DXF only for actually flat-cut panels, drawings and a small parts list identifying every piece as temporary or permanent. Use the same canon and coordinate registration as the selected plates. For multipart tools, supply one valid connected solid per manufacturing part plus a labeled assembly; do not put the full tool assembly into a single-part plate upload file.\
\
Include the documented tool material/process, critical fit and flatness requirements, orientation, thickness, separation/joining details, local cost/quote basis if actually available, and a short illustrated rear-fill procedure. Model the tool even when printing is performed elsewhere; do not stop at the sentence “contractor to make a form.” Never upload or order without the existing required approval.\
\
If the form is unnecessary, infeasible, or has a specific unresolved conflict, provide the concise evidence-based reason, a section view, and the simpler supported repair/installation alternative. Document the specific form geometry and feasibility findings; a generic mortar-repair instruction is not sufficient.\
\
Release the main and diverter plate fit-trial files independently when this tool does not change their requirements. Do not delay usable plates for optional form cosmetics or full-wall remodeling. If the SELECTED form-assisted repair changes an essential plate aperture, locator or finished-plane dimension, resolve that specific dependency and regenerate the affected files before labeling that version ready. The owner should receive one recommended repair route, not an unresolved gallery of molds.\
\
\## 9. Deliver small, evergreen, audience-specific packages\
\
Use the next unused release identifier consistently. Keep selected manufacturing files separate from assembly references and historical alternatives.\
\
\### Fabricator / ordering\
\
Produce one clearly identified \`METAL_FIT_TRIAL\` folder and, if useful, one alternative \`CLEAR_FIT_TRIAL\` folder. Each contains only the selected standalone main and diverter. One part's STEP/DXF/STL are alternative file representations, not additional parts to purchase.\
\
For each active part supply:\
\
\- STEP containing exactly ONE connected valid custom solid, mm units, local origin at the outer circle center, back Z=0 and front Z=actual scenario thickness. Document +Y and front/back. No wall, factory trim, assembly offsets, loose tabs or duplicate bodies.\
\- Matching clean 1:1 DXF of actual cutting contours. No annotation, hidden construction lines, duplicate/open loops, mirrored holes, toolpaths or unrequested kerf compensation. Slots and tab transitions must be part of the real profile, not a drawing overlay.\
\- Optional STL for a useful fit print, not as the default precision sheet-cutting file.\
\- A dimensioned PDF showing profile, apertures, actual locator centers/slot details when selected, relevant local datums, thickness, material/finish, tolerances, edge requirements, quantity and revision. Distinguish nominal design values from verified vendor capability.\
\- Isolated top and oblique previews from those exact exported parts.\
\
Add concise shop notes, an exact one-line-per-part upload list and hashes of the actual outgoing bytes. Zip each alternative route separately. Do not include the historical plain/tabbed/120 mm/3 mm variants in the same upload archive. Confirm thickness and cosmetic/edge expectations before purchase. No exact brushed-nickel color match is assumed.\
\
\### Repair tooling, when justified\
\
Keep \`REPAIR_FORM_TRIAL\` separate from both plate-order archives. State that the form is a construction tool, whether it is actually recommended for this installation, and whether its use changes any plate-order requirement. Include the section 8 assessment even if no tool is recommended. Do not confuse the removable centering aid, flat clear fit-trial plate, and rear-fill form: they have different purposes and acceptance checks.\
\
\### Owner\
\
One-page \`ORDER_AND_NEXT_STEP\` in readable HTML/Markdown/PDF: recommended design, selected/default material route, exact two files and quantities, how to upload one format per part, any actual cost/lead-time information, and the short fit checks before permanent installation. Explain the bolt/slot or no-tab decision in one annotated view. State separately whether to obtain/use the repair form and what it would achieve. Do not make the owner choose among unresolved engineering experiments.\
\
\### Plumber\
\
\`PLUMBER_START_HERE.pdf\`, approximately 2–3 readable pages, plus editable source: model identities, actual front and rear photographs, correct part/fastener order, three depth branches, support/seal detail, adapters/hardware to check or bring, and a short success/failure checklist. Include a draft pre-visit message; do not send it. Coordinate any recommended form-assisted repair with the mason/repair contractor and the final plumbing position; link a separate short form setup/removal sheet rather than cramming it into the plumber brief. No required new dimensional survey.\
\
\### Installation and maintenance\
\
A concise illustrated \`INSTALLATION_GUIDE.html\` and PDF with editable source. Each step has a concrete action, location, material/tool, responsible person, completion check and relevant pitfall. Include incoming-part inspection, protected dry fit, centering/retention, conditional support repair, sealing/cure, factory assembly, function/drain/water checks, and future service. Use actual photos or current CAD renders, not generative depictions. Include sections through the real mounting studs/tabs as well as both controls. For the selected form-assisted route, add the front/rear forming and demolding sequence and show the final supported wall with all temporary tooling removed.\
\
\### Template and engineering record\
\
Supply a calibrated tiled US-Letter template with overlap registration and two-axis scale bars, plus an optional large-sheet version. The 220 mm main plate does not fit across Letter's 215.9 mm short side. Use separate clearly labeled reference overlays for the cover/gasket and cuttable profiles; instruct 100% printing and physical scale checking. Paper tests XY only; a relevant depth test uses the actual thickness.\
\
Keep a short design-decision report: final measurement import, transforms, chosen/rejected locator design, actual feature sizes and clearances, gasket/coverage results, uncertainty scenarios, remaining physical checks, and revision dependencies. Include an updated portable Blender scene and local HTML review, not a new dashboard platform. Keep current geometry and actual-source textures correctly linked.\
\
\## 10. Independently validate the files and finish this run\
\
Generate all selected geometry, drawings, views and checks from the active canon/design source. Ensure all active outputs use the accepted measurements, confirmed feature statuses and selected geometry. Keep superseded values and designs in the engineering history, outside active ordering instructions.\
\
Reimport the actual deliverables and check units, placement, bounds, thickness, topology, hole/slot locations and count, aperture/profile matching, connected tab ligaments, and correspondence among STEP, DXF, drawings and previews. Verify no geometry exists only in Blender. For tabbed designs use the actual boolean result/profile area in volume checks, not the unmodified plain-capsule formula. Validate plain and tabbed pipelines on appropriate cases without changing accepted measurements.\
\
Test orientation explicitly: front-view A is upper-right; B is lower-left. A back view may look mirrored, but the manufacturing transform must not accidentally be mirrored. Check the selected slot axis against the intended spacing vector. Check actual ZIP contents and outgoing hashes, not only a design report.\
\
Reopen the scene and HTML, render and inspect the documents/templates, and issue a brief adversarial review covering locator interference, insufficient land, underconstrained centering, constrained assembly, stale data, wrong stock, and misplaced manufacturing geometry. Correct problems; do not equate a successful export with physical fit.\
\
For a selected repair form, also validate its exported part count, as-cast envelope, front-face datum, supports, protected hardware, placement and extraction paths, and agreement with the chosen repair material/sequence. A passing form check is not proof of cured wall strength or waterproofing. Keep tool readiness and permanent-installation checks distinct.\
\
Use only the readiness distinctions necessary:\
\
1\. \*\*Fabrication/fit-trial files ready:\*\* the selected files are coherent, manufacturing-feasible and have no known disqualifying conflict; remaining physical checks are specific and reasonable.\
2\. \*\*Owner order approval:\*\* upload and purchase require separate authorization.\
3\. \*\*Physical fit established:\*\* actual received parts and correct factory components assemble, center, seat, remain supported and permit operation/removal.\
4\. \*\*Permanent use established:\*\* suitable support and sealing, correct assembly, required cure, function/drain checks and actual water tests have been completed.\
\
The goal of THIS RUN is stage 1 plus a complete practical handoff for stages 2–4. Do not wait for manufactured parts or a future plumber visit to deliver that work. Do not claim the future stages happened. If one proposed locator fails, finish a justified fallback; if only the diverter is blocked, release the main. Ask another measurement only under the narrow exception in section 5.\
\
Finish with direct paths to the chosen route packages and upload list, the final accepted measurement table, a single explained main-design decision, the owner/plumber/manual files, the repair-form decision and any selected tool package, a brief list of actual physical checks, and the new commit/revision. The owner should be able to order the appropriate plate set next, not commission another research phase.\
\
\## Primary references to verify when needed\
\
Use applicable archived documents first, with current official verification for consequential specifications and current supplier offerings. Keep dated source attribution in the technical record, not time-sensitive narration in the everyday instructions.\
\
\- Kohler stacked trim: https\://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf\
\- Alternate stacked-trim revision: https\://techcomm.kohler.com/techcomm/pdf/1216755-2.pdf\
\- Diverter trim: local \`data/evidence/kohler-diverter-trim-install-1190382-2.pdf\`; official lead https\://techcomm.kohler.com/techcomm/pdf/1190382-2.pdf\
\- K-2973-KS drawing: https\://techcomm.kohler.com/techcomm/pdf/K-2973-KS_spec_US-CA_Kohler_en.pdf\
\- Service parts: https\://resources.kohler.com/onlinecatalog/pdf/1041507_5.pdf\
\- Stud 1038645: https\://www\.kohler.com/en/support/find-a-service-part/shop-parts/stud-10-24-x-4-56-l-1038645\
\- Acrylic: https\://sendcutsend.com/materials/acrylic/\
\- Stainless: https\://sendcutsend.com/materials/stainless-steel-316/ and https\://sendcutsend.com/materials/stainless-steel/\
\- Protected brushed alternative: https\://www\.oshcut.com/materialdetails/stainless-steel-304-4-finish-with-top-film\
\- Fabrication requirements: https\://sendcutsend.com/guidelines/sheet-cutting/\
\- Repair material research lead, not approval for this particular substrate or form: https\://www\.ctscement.com/product/cement-all ; obtain the current datasheet and compatibility guidance for the selected method.\
\- General locating-design background, not a prescribed purchased component: https\://www\.carrlane.com/engineering-resources/technical-information/manual-workholding/locating-devices/locating-pins