Act as my local reverse-engineering, CAD, and repair-planning agent. Execute this project, not merely a plan.

**Project repository:** `~/Code/shower-kohler-valve`

**Original Polycam photogrammetry exports:**

```text
~/Downloads/shower-hole-valve-polycam.zip
~/Downloads/plates-side-1-polycam.zip
~/Downloads/plates-side-2-polycam.zip
```

The wall-and-valve capture, `shower-hole-valve-polycam.zip`, is my best and most accurate scan. Make it the primary spatial reference for the actual installation: mounting/bolt features, installed valve position and orientation, wall opening, grout gouges, overcuts, and surrounding tile. The two plate-side scans look distorted, likely because of reflective metal. They are secondary references, not equally trustworthy scans to average into the wall capture. Inspect what each actually contains; filenames alone do not establish which component or face is present.

Use Blender as the application I open to understand and inspect the project. Use CadQuery behind the scenes for authoritative parametric manufactured geometry and fabrication exports. Retain a simple HTML review so I do not need Blender proficiency to answer measurement questions.

I want a faithful, measurement-validated model of this particular installation that supports:

1. Exact manufacturing specifications for a custom escutcheon/backing plate, if that proves appropriate.
2. Reconstruction of the actual wall opening, individual overcuts, installed valve/hardware, Kohler inner plate and gasket, and outer trim.
3. Demonstrated coverage, centering, gasket support, mechanical clearance, and feasible installation/removal.
4. A contractor adjustment schedule and an illustrated, near-“IKEA-simple” repair manual, using readily sourced materials plus the custom part where justified.
5. A self-contained project another capable assistant, including GPT-6 Astra, can interrogate and independently audit without this conversation.

**Constraints:** Preserve the existing travertine. No further tile cutting, grinding, drilling, enlargement, or retiling without a specifically approved exception. Supported local rebuilding with appropriate mortar, stone patches, backing, or other materials is potentially acceptable. Retain the original Kohler components and their intended sealing, mounting, drainage, and service functions. A custom plate is a candidate, not a predetermined answer.

The reported problems are an oversized opening, saw cuts outside the decorative trim, a wall-facing inner-plate gasket without a continuous landing, and studs that may prevent the outer trim from seating. Plastic piping may be replaced with copper; establish what has actually happened since the scans rather than assuming planned changes are complete.

Earlier suggestions of model K-T14489-4, a 7¼-inch outer trim, 8- or 8¼-inch backing plates, and ⅛-inch backing-plate thickness are research/design leads unless separately confirmed. Earlier generated repair images are not evidence of dimensions, hidden construction, or a valid assembly.

## 1. Execution order and autonomy

Follow this sequence:

**Repository and evidence preservation → complete provisional reconstruction → Blender/HTML review and exact measurement worksheet → accepted measurements and model update → independent checks and repair selection → physical fit verification → fabrication package and illustrated manual.**

Use my scans, genuine photographs, existing confirmed measurements, and applicable online manufacturer images/documentation/CAD to build the provisional assembly first. Do not begin by making me measure everything the evidence can already resolve. Unknown critical details may be represented provisionally and visibly labeled; do not spend days polishing guesses.

Ask early only for missing access, essential input identification, permission, or a minimal scale/identity check without which useful reconstruction is impossible. Otherwise derive measurement questions from the provisional model.

Keep progressing through ordinary installation, script, mesh, and rendering problems using reasonable documented fallbacks. Optional tools or one unknown dimension must not block independent work. Do not reduce the first deliverable to folders, an installation report, or a future plan when accessible evidence permits modeling.

Be explicit about what was executed, inspected, estimated, and physically verified. “Precision” means enough demonstrated accuracy for the specific decision, not a convincing render or many decimal places. Keep geometric fit, physical fit, fabrication approval, and installed water performance as separate conclusions.

## 2. Create the repository and preserve the scans

Work on the machine/filesystem that actually contains the specified home-directory paths. Expand `~` correctly. If execution is isolated from my computer, report that access limitation; do not create an unrelated look-alike directory and claim the project or scans have been initialized on my machine.

Inspect `~/Code/shower-kohler-valve` before writing. Create it if absent. If it already exists, inspect its Git state and preserve files, local changes, branches, history, remotes, and hooks. Avoid accidentally initializing inside an unrelated parent repository. Initialize a new repository with branch `main` when appropriate; do not reset or reinitialize existing work destructively.

### Git and large-file policy

Install Git if needed through trusted, current instructions. Use ordinary Git for this project; do not install, configure, or use Git LFS. Preserve existing hooks and shared hook configurations. Do not change global Git identity or configuration unnecessarily.

**Store the actual original ZIP files inside this repository and version their complete contents directly in ordinary Git.** They must not be untracked files, external Downloads links, pointers, or a manifest-only substitute. Track the original ZIPs and selected binary deliverables, such as `.blend` snapshots, as ordinary Git blobs alongside scripts, parameters, manifests, and text reports. Before staging, check applicable Git attributes and ensure these paths are not assigned an LFS filter; preserve unrelated attributes and hooks.

Copy—not move—the three archives to:

```text
data/raw/polycam/shower-hole-valve-polycam.zip
data/raw/polycam/plates-side-1-polycam.zip
data/raw/polycam/plates-side-2-polycam.zip
```

Compare SHA-256 hashes and sizes before and after copying. Preserve original names and bytes. If a destination already exists with a different hash, keep both versions under documented identities rather than overwriting evidence. Never modify or repack the originals.

Create an input manifest recording source path, repository-relative path, hash, size, role, available capture/export metadata, and known limitations. Distinguish actual capture dates from filesystem modification dates. Record my scan-quality assessment as an assessment, not a calibrated accuracy claim.

Inspect archive contents and available disk space before extraction. Extract into separate reproducible directories, preserving OBJ/MTL/texture relationships. Protect against path traversal, escaping symlinks, and unsafe archive entries; do not execute files from an input archive. Do not assume the archives contain OBJ until inspected.

Use this structure, adapting only when existing work warrants it:

```text
shower-kohler-valve/
  README.md
  START_HERE.md
  AGENTS.md
  project                     # simple working command wrapper
  .gitignore
  environment/                # version records and reproducible dependency files
  data/
    raw/polycam/              # original ZIPs, tracked directly in ordinary Git
    evidence/                 # supplied photos and applicable manufacturer sources
    extracted/                # reproducible extraction; ignored by Git
    derived/                  # reproducible scan processing; ignored by Git
  canon/
    inputs.json
    measurements.json
    features.json
    transforms.json
    design_decisions.json
    source_register.json
    project_state.json
  src/
    cad/                      # authoritative CadQuery models
    blender/                  # scene-building and rendering scripts
    analysis/                 # registration, coverage, fit, and query logic
    review/                   # HTML/manual templates and generation
  scripts/
  tests/
  build/                      # temporary/regenerable outputs; ignored by Git
  deliverables/
    current/
      blender/
      review/
      cad/
      drawings/
      manual/
      analysis/
      manifest.json
  docs/
    decisions/
    validation/
    physical_checks/
    downstream_audit_prompt.md
```

Keep source, accepted observations, evidence, and a reviewable current deliverable snapshot versioned. Do not commit extracted copies of all three archives, every intermediate mesh/render, environments, caches, logs containing secrets, or Blender backup files. Keep build caches separate from the selected deliverables. Do not pack duplicate full-resolution scans into the Blender file unnecessarily; use repository-relative references and a documented restoration process, or a deliberate self-contained snapshot when needed.

Verify with `git ls-files` that all three originals are tracked. Read their bytes back from the committed Git objects and compare SHA-256 hashes and sizes against the input manifest. Run `git fsck` and test a clean local clone to confirm the original archives and selected deliverables are recoverable without the Downloads copies or Git LFS. Pointer files are not completed scan preservation.

Make meaningful commits: initial project and preserved inputs, first reconstruction/review, accepted measurement revisions, and validated design/manual milestones. Inspect staged changes before committing. Reuse an existing valid Git identity. If none is configured, ask for the missing identity without inventing one; continue the modeling and leave clearly identified changes ready to commit. Do not disable signing or other security settings merely to force a commit.

Do not create a GitHub repository, add a remote, push, publish scans, or upload to a third party without approval. Local Git is not an off-machine backup. For transfer or backup, use a full clone or a self-contained Git bundle containing the relevant commits, including the complete committed original ZIPs and selected deliverables. Preserve required uncommitted files separately and verify a restored checkout against the input manifest. Do not prune raw evidence or rewrite history without explicit approval.

After import, all normal work must use repository-relative paths. The project must remain rebuildable if the original Downloads copies disappear. Test that restoration/rebuild path, not merely the working session in which it was created.

## 3. Set up Blender and CadQuery

Detect the OS, processor architecture, available tools, and existing installations. Prefer stable, compatible open-source releases from official sources. Reuse suitable software rather than installing duplicates. Record tested versions and lock the working environment; do not pin speculative versions before checking availability and compatibility.

**Blender:** primary visual workspace, scan inspection, named assembly, exploded/section views, worksheet illustrations, and manual rendering.

**CadQuery:** authoritative parametric solids for the custom plate and fit-critical reconstructions. Accepted parameters generate manufacturing geometry and corresponding Blender display meshes.

Keep CadQuery in an isolated Python environment. Run Blender with its own supported Python environment/process; exchange geometry and structured metadata rather than forcing CAD dependencies into Blender’s bundled Python. Provide working launchers that hide these details from me.

FreeCAD, CloudCompare, and lightweight mesh/DXF/browser libraries are optional. Add one only for a specific useful task. Do not make me operate multiple applications. If CadQuery setup fails after a reasonable attempt, use a documented open-source CAD fallback while retaining Blender as the visual workspace and one dimensional master.

Do not replace system Python, remove existing applications, change security protections, or install paid trials. Ask only for genuinely necessary elevation or approval. Avoid compiling a large toolchain when a supported binary environment works.

Before the full build, test a known-size part with an offset hole and asymmetric orientation marker. Export CAD and display geometry, reimport it, and verify dimensions, hole position, orientation, and scale in Blender and the review. Test script execution, `.blend` saving, and a simple render. Use a CPU/static fallback if GPU rendering or WebGL fails.

Implement a small command wrapper rather than a sprawling framework. These commands, or equally simple documented equivalents, must actually work:

```text
./project doctor
./project ingest
./project build
./project review
./project import-measurements <response.json>
./project validate
./project query <operation> [arguments]
./project handoff
```

Re-running them should preserve accepted data, reuse unchanged work, and regenerate only stale results. `build` must not silently overwrite user measurements or independent manual edits.

### Optional Meshy access

I have Meshy API access, but do not use it automatically. Prefer local scans and parametric reconstruction. Use Meshy only for a demonstrable benefit, with explicitly authorized credentials, upload permission, and spending limits. Do not search my unrelated files for keys, log credentials, or assume API access authorizes sending home scans.

Generated/remeshed output cannot establish physical scale, missing holes, unseen surfaces, or damaged-wall boundaries. Inspect the current API; do not rely on obsolete parameters. Disable automatic/AI sizing where applicable, preserve originals, and verify transforms and feature deviations. Reject derivatives that alter critical evidence beyond the recorded error allowance. Optional Meshy failures must not block this project.

## 4. Establish source priority feature by feature

Use `shower-hole-valve-polycam.zip` as the primary installed reference. Extract the actual opening, wall/grout damage, mounting features, control axes, protrusions, and their relationships wherever genuinely visible. Define stable IDs for individual gouges and fastener features.

Do not let an automatic global fit to the lower-quality plate scans move the primary wall/valve arrangement, straighten the installed valve, or erase the actual cuts. Evaluate local feature quality: even the best scan can contain reflective-metal errors or occlusions.

For `plates-side-1-polycam.zip` and `plates-side-2-polycam.zip`, determine which parts and faces are present, which features are credible, and which are distorted or missing. Use credible portions for component shape and corroboration. Keep unreliable portions visible as uncertain references or exclude them from dimensional fitting with an explanation. Do not merge sides into one supposedly accurate model merely because both exist.

A visible bolt head is not proof of the underlying hole’s exact diameter or axis. A captured stem is not proof of hidden threads or engagement. Use observed features to estimate the installed relationships; resolve critical unknowns with documentation and the later worksheet.

Accepted physical measurements govern the actual parts and can correct the scan. Applicable manufacturer dimensions govern documented nominal design, not automatically the present installation. Preserve conflicts and explain them instead of averaging incompatible sources.

Research official Kohler identities/revisions, installation instructions, parts diagrams, dimensioned drawings, and available CAD. Confirm that a model or document applies to the actual hardware. Public product photos are form/identity evidence, not precision rulers. Do not scale drawings marked not to scale or assume marketing/BIM geometry contains hidden mating details.

Save relevant documents/images where permitted and record URLs, title, revision/page, applicability, and supported claims. Do not use generative images or generic “similar” parts as dimensional evidence. Avoid broad downloads unrelated to this installation.

## 5. Coordinates, registration, and distinct states

Use millimeters in the canon and CAD. Preserve original units and document every scale conversion.

Define a right-handed installed frame viewed from inside the shower: +X right, +Y up, +Z out from the wall. Establish a reproducible origin tied to a valve feature and a reference plane fitted to appropriate intact stone. Record fitting regions and residuals. Distinguish the reference plane from real tile topography, grout recesses, lippage, and wall tilt.

Record local part frames and explicit transforms into the installed frame. Blender may use its usual Z-up convention and meter-based coordinates, but the CAD-to-Blender/browser mapping must be explicit, tested, and applied once. Do not infer physical scale from a viewport grid or unit label. Verify an asymmetric test part and known dimension across all representations.

Check scale with independent dimensions in different directions and depth where possible. Use documented rigid or uniform-scale registration. Do not silently stretch scans nonuniformly to make dimensions agree. Report feature-level deviations, not only whole-model RMS.

Use shared credible features or documented mechanical constraints to place separately scanned components. Circular symmetry may leave rotation ambiguous; use non-symmetric features where available. A registration cannot establish an installed relationship that was never observed or otherwise constrained.

Maintain separate scene/model states:

- **As observed at capture:** actual damage and hardware pose, including misalignment.
- **Manufacturer-intended assembly:** documented arrangement and its applicability.
- **Proposed repairs:** explicit changes to supports, surfaces, hardware position, and new parts.
- **Selected arrangement:** the reviewed design, with physical verification status.

Never improve the as-observed geometry by secretly moving the valve, flattening the wall, filling gouges, or shortening studs. Track later physical changes as new states and invalidate affected checks. Distinguish the outer trim center from either control axis, the mounting-hole midpoint, and the irregular opening’s center.

## 6. Reconstruct the installation and build the Blender scene

Use a hybrid model: parametric manufactured parts and contact features, plus preserved mesh geometry for irregular wall damage. Do not turn millions of triangles into a faceted STEP solid and call it precision reconstruction. Preserve full-resolution evidence; use explicitly labeled display proxies for responsiveness without relying on them for fine coverage checks.

Create three primary separate models:

1. **Kohler inner plate:** outline, thickness versus formed depth, bends/recesses, slots/holes, hubs, fastener seats, rear protrusions, and gasket interface. Front/back must be unambiguous.
2. **Kohler outer trim:** actual outline/diameter, rear cavity, rim/contact plane, control openings, drainage features, and relevant fastening/handle interfaces.
3. **Custom backing plate candidate:** justified outer profile, aperture(s), required holes/features, thickness, edge/flatness requirements, and support/seal interfaces.

The existing Kohler models are reference reconstructions, not replacement parts to fabricate. Only the custom plate is for manufacturing unless I change scope.

Also represent:

- The installed valve, both control axes, studs, nuts, adapters, hubs, accessible supports, and relevant clearance/engagement envelopes. Do not invent hidden valve internals; detailed helical threads are unnecessary when envelopes and engagement dimensions suffice.
- The original gasket’s actual contact path, width, free thickness, notches, and condition where known. Separate a documented installed compression requirement from guessed rigid-body overlap.
- Each wall opening, saw kerf, missing stone edge, grout recess, and uncertain texture/shadow feature. Preserve observed depths; mark unobserved depth unknown.
- Candidate sound support/sealing lands, nearby obstructions, and proposed backing, patch volumes, sealant or membrane layers. Keep proposed construction separate from unknown concealed construction.

Organize Blender into clearly named collections for source scans, observed wall/valve, reconstructed inner plate/gasket, outer trim, custom plate, proposed repair materials, datums/measurements, and cameras. Give components stable feature IDs and evidence/revision metadata.

Create saved views for front orthographic coverage, inner-plate front/back, assembled trim, exploded order, gasket contact, and sections through the studs and both control axes. Provide easy collection toggles and consistent part colors; uncertain geometry must be visibly distinguishable. Do not leave me with an unlabeled imported mesh pile.

The custom plate displayed in Blender must be exported from the same CAD geometry used for STEP/DXF. No independently edited visual duplicate. If a Blender edit changes fit-critical geometry, record it as a proposed parameter change, rebuild the master, and refresh all dependent files.

Record tessellation settings and the display-mesh approximation allowance. CAD dimensions are queried from CAD/parameters, not inferred from smooth shading. Exploded display offsets and ghost views must never change the actual assembly placements or be exported as manufacturing positions.

Save a usable `.blend` snapshot with working asset paths, sensible initial camera/view, lighting, and layer controls. Verify it can be reopened. Preserve user-created notes/cameras in a separate collection or configuration during rebuilds. All required assets must reside in the repository or be reproducibly restored there from the tracked archives, not depend on Downloads.

## 7. Measurement canon and uncertainty

Maintain machine-readable measurements, source register, feature registry, transforms, design decisions, and dependencies. Each important observation needs:

- Stable ID, component/state, exact datum/endpoints, method, and fit-critical purpose.
- Raw readings, original units, accepted value in millimeters, source, date/revision, and any supporting photo.
- Uncertainty/bound with a defensible basis, or explicitly unknown.
- Status: user-confirmed, manufacturer nominal, scan-derived, inferred, unknown, conflicting, or superseded.

Keep accepted physical measurements separate from proposed design dimensions, provisional assumptions, manufacturing tolerances, registration uncertainty, and mesh approximation. Caliper resolution is not demonstrated measurement accuracy. Do not invent confidence percentages or assume all errors are independent.

Preserve inconsistent observations and request the smallest useful recheck rather than silently overwriting or averaging them. Never replace a confirmed measurement with a prettier scan fit. Corrections must propagate to geometry, validation, worksheet predictions, drawings, and exports.

Define which accuracy is needed for each decision. A generous outer cover margin and a close screw-hole fit need different validation. Missing critical values are unknown, not zero or a typical dimension presented as fact.

Use actual measurements only once as evidence: agreement with the same measurement used to fit a model is not an independent validation. Reserve suitable cross-checks or physical fit tests. If a check later becomes a fitting input, mark that change.

## 8. Deliver the model-derived HTML measurement worksheet

After substantial provisional reconstruction, generate `deliverables/current/review/index.html` and a printable worksheet. Use views rendered from the real project and annotated original photographs, never generative art. Show what exists, what is inferred, and what each requested measurement would resolve.

Provide an interactive 3D view when practical, with static image fallbacks, front/back/side/section views, layer toggles, assembly/explode controls, and observed-versus-proposed comparison. Bundle dependencies or use a localhost-only launcher; no public hosting or cloud upload. Test the page at readable sizes. Browser mesh-point measurements must be labeled approximate rather than exact CAD queries.

Each measurement request must include:

- A stable ID and labeled tool-contact points/arrows on the actual component.
- Plain-language instructions showing where the caliper jaws, straightedge, ruler, or depth gauge go.
- A provisional prediction labeled as an estimate, the useful accuracy needed, and the consequence for fit/design.
- Blank fields for raw reading, units, tool/method, repeat readings where useful, and notes/photo reference.

Provide the complete tailored worksheet, highlighting roughly 6–8 highest-value first checks. Prioritize the inner plate’s hole/slot positions relative to reproducible edges/datums, near/far hole boundaries, formed offsets, rear protrusions, gasket footprint, and fastener locations. Include wall scale, worst gouge extents, valve pose, trim center, and stud/depth relationships.

Do not simply ask me to “measure the center.” Show how measured edges and diameters determine a center or hole spacing. Provide alternatives when an irregular edge is a poor datum, a feature is inaccessible, or the plate exceeds my caliper’s range. Do not deform the gasket or damage finishes. Assign inaccessible pressure-containing-plumbing measurements to the installer.

Provide a copyable response block and JSON export/import containing project ID, review revision, measurement IDs, units, and raw observations. Browser fields do not update the CAD automatically unless you implement and test a local save path; explain the actual handoff.

When I reply, incorporate accepted observations into the canon, preserve history, update the model, and regenerate all affected outputs. Highlight changed conclusions. Ask a focused second batch only when necessary; do not repeat answered questions or treat silence as confirmation.

## 9. Prove coverage, centering, support, and assembly

Implement reproducible checks with feature IDs, state/revision, numerical result where justified, uncertainty allowance, criterion, source, and PASS / FAIL / UNRESOLVED. Highlight the limiting location in a view. Missing evidence is not a pass, and unresolved fabrication questions must not block drafts.

**Coverage:** Trace and identify every actual gouge/overcut. In orthographic views, overlay damage regions, the original trim, candidate plate outline and aperture(s), and sound support/seal regions. Compute the minimum remaining coverage margin for each damaged feature, not merely total covered area. Distinguish visual concealment from adequate sound landing beyond the damage. Evaluate depth/oblique visibility where the actual geometry makes it relevant.

**Centering:** Locate the custom plate relative to the actual Kohler outer trim and installed pose. Report X/Y offsets, rotation, and minimum/maximum visible border. Explain what physically locates and retains the part; a plate dragged into position in Blender is not proof of repeatable centering. Check permissible installation adjustment without losing coverage or support.

**Gasket and sealing interfaces:** Show the entire original gasket landing, including unsupported/recessed segments and nearby apertures. Separately show the new plate’s support and its sealing path on existing material. Quantify land width/flatness where observable. Do not infer adhesive bond, stone soundness, sealant performance, or gasket compression from a collision-free render.

**Mechanical fit:** Check studs/nuts, hubs/recesses, outer cavity, mounting clearances, adapters, thread engagement, handles, drainage, cartridge access, and complete depth stack including new plate and installed seal layers. Test feasible installation/removal paths and tool access, not only the final pose. No casually cutting studs or discarding the factory inner plate to resolve a clash.

**Support:** Establish how the custom plate and any patch are retained and supported. Assess consequential unsupported spans and deformation using defensible inputs/calculations or a targeted fabricator/physical check. Thickness or a bead of silicone alone does not establish structural adequacy.

Use an explicit error allowance for scan scale, feature reconstruction, registration, physical measurement, fabrication, installation placement, and numerical/tessellation approximation. Margins smaller than unresolved error are not demonstrated passes. Handle shared errors sensibly rather than adding spurious statistical certainty.

Derive useful plate sizes from actual damage and required support/seal allowances. Do not assume 8 inches is sufficient. If the trim is confirmed at 7¼ inches, an 8-inch concentric backing plate adds ⅜ inch per side, not ¾ inch; that is still not the overlap on intact stone. Preserve this distinction in all dimensions and illustrations.

## 10. Select the repair and specify contractor adjustments

Compare only genuinely plausible alternatives: applicable factory adjustment, custom backing plate, supported local rebuilding, or a combination. Do not force the custom plate if evidence shows another no-cutting solution is better.

For each viable option, identify required changes, access, material interfaces, dimensions/volumes, appearance, serviceability, unresolved conditions, and disqualifiers. Prefer the least disruptive durable solution supported by the evidence.

Document the verified layer order. A candidate is existing wall → new plate’s wall seal → custom plate → original wall-facing gasket and inner plate → outer trim/handles; verify actual component order and permitted assembly from the applicable instructions.

Do not automatically copy every factory screw hole into the custom plate. State the purpose of each proposed aperture, clearance hole, mounting hole, counterbore/countersink, or thread. Omit unnecessary openings that undermine gasket support or water sealing. Preserve required service access.

Produce a contractor adjustment schedule: current versus proposed position, datum, supported target/range, responsible trade, prerequisites, and an on-site check. A valve move must state translation/rotation and physical feasibility; do not reposition plumbing merely to improve a rendering. Verify stud/adapter adjustments before proposing destructive changes.

Separate cosmetic coverage, rigid support, surface water sealing, and concealed waterproofing continuity. The scan cannot establish hidden deterioration, bonding, an unseen membrane connection, or the sole cause of the previous leak. Specify the smallest useful inspection for each consequential unknown and continue independent work. Do not silently relax the no-cutting constraint.

## 11. Physical verification and manufacturing package

Create a 1:1 printable profile template with orientation, datums, hole IDs, and two-axis calibration marks. Explain 100% printing and a measured scale check. Paper/card verifies planar alignment/coverage only; provide a thickness-accurate mockup or spacer dry fit for the depth stack. Prototype materials are not approved permanent wet-area materials.

The dry-fit record must check actual valve registration, centering, worst gouges, support/rocking, gasket landing, outer-trim seating, hardware engagement, drain orientation, handle travel, and removal/tool access. Record results/photos against the revision and revise failures. Do not claim physical tests occurred without results.

Confirm the actual fabricator’s capabilities, process, file formats, material/finish, thickness, achievable hole/flatness tolerances, edge treatment, and design constraints from current documentation or authorized correspondence. Draft any needed inquiry; do not send it without permission.

Generate and reimport/validate:

- Separate STEP models for the custom part and the two Kohler reference reconstructions.
- An assembly STEP with components separate and correctly placed, not fused. Supply the irregular wall mesh alongside it; label any CAD wall surrogate’s limitations.
- A true-size DXF containing only the custom plate’s required fabrication contours/holes. No annotations, preview circles, warning text, duplicate edges, or inspection outlines in the cut paths.
- A dimensioned PDF with units, datums, hole coordinate schedule, relevant hole types/depths, thickness, material/finish, edge/flatness requirements, tolerances, orientation, revision, and manufacturing notes.
- The matching Blender/GLB representation and fit-template/mockup files where useful.

Keep the clean cutting file separate from the drawing. STEP/DXF and the Blender part must agree with the same canon and design. Validate units, bounds, solid validity, contour closure, hole count/positions, placements, and conversions. Inspect rendered PDFs/HTML for legibility and incorrect dimensions. Follow available document-generation instructions when applicable.

Mark incomplete outputs DRAFT / NOT FOR FABRICATION through filenames, drawings, and manifests, not cuttable DXF text. Maintain separate readiness fields for geometric checks, materials/design review, physical fit, explicit fabrication approval, received-part inspection, and installed leak testing.

Do not generate machine-specific G-code, place orders, contact fabricators/contractors, or transmit files without authorization. After manufacture, provide an incoming-inspection checklist for dimensions, hole positions, flatness, thickness, burrs/edges, and finish before permanent installation.

## 12. Write the illustrated repair and installation manual

Produce a self-contained HTML/PDF manual with editable source and illustrations from the selected, revisioned geometry or annotated original photos. Develop a draft early, but do not present unresolved work as approved instructions.

Keep the homeowner sequence short and visual, with evidence and alternatives in appendices. Each step needs its prerequisite, responsible person, named tools/materials, one concrete action, an exact-location image, a checkable completion condition, and the relevant pitfall/stop condition. Do not omit curing, access, or testing to make it appear simple.

Research current official technical data and actual purchasing sources for selected materials. Prefer readily sourced products, including Home Depot where appropriate; verify rather than assume local stock. Document product/version, purpose, quantity basis/waste allowance, substrate and wet-area suitability, vertical/application-thickness limits, preparation/primer/reinforcement, working/cure/water-exposure requirements, and acceptable substitutions.

Show where any backing, patch, bonding layer, membrane, sealant, or gasket goes, its support, and the access needed to place it. Grout, repair mortar, adhesive, structural backing, waterproofing, sealant, and gaskets are different functions. Do not prescribe filler bridging an unsupported opening or imply a surface patch restores an unknown concealed membrane.

Include protection of valve/service parts, plumbing changes/testing before final positioning, support/rebuild where justified, dry fit, surface preparation, selected sealing, correct factory hardware adjustment/assembly, curing, incoming/final inspections, leak checks, and future access. Derive the actual sequence from materials and manufacturer instructions.

Address the project’s real pitfalls: discarding the inner plate, assuming the outer cover replaces the gasket landing, marginal coverage without sound overlap, forcing trim onto interfering studs, unnecessary holes, encased service parts, blocked drainage, inadequate handle engagement, and unverified water-sealing assumptions. Do not invent torque, compression, cure times, or minimum bonds.

Separate appropriate homeowner actions from pressure-containing plumbing, soldering, structural, or waterproofing work needing qualified help. Verify jurisdiction before making local-code claims. Give the homeowner a checkable result for professional tasks rather than an unsafe shortcut.

Specify cure-dependent checks that distinguish supply/valve leaks from water entering around the assembled trim, with access and stop conditions. Do not claim that a successful local test certifies the entire concealed shower system.

## 13. Make the project interrogable and auditable

`START_HERE.md` must identify selected state/revision, evidence priority, accepted versus unresolved facts, current readiness, approvals, exact file paths, and next action. `AGENTS.md` must preserve the scan hierarchy, canon rules, command entry points, and repository practices for later assistants.

Provide stable machine-readable feature IDs, damage contours, support/sealing regions, accepted measurements, transforms, design choices, and computed checks. Add `questions_answered.md` addressing coverage, centering, gasket support, studs/depth, repair materials, installation feasibility, and serviceability with links to evidence and computations.

Implement simple query operations for listing features, reading a dimension with provenance, measuring named features, reporting coverage/clearance, generating a section, comparing states, and rerunning validation. Results must identify units, state/revision, approximation, and unresolved assumptions. Exact solid queries, approximate mesh queries, and merely reviewed reports must not be confused.

Include a compact downstream audit prompt and manageable analysis package with annotated views, computed results, materials evidence, and an installation dependency sequence. Do not assume another assistant can directly parse STEP or open a huge `.blend`. It should be able to review evidence without executing CAD and recompute it when suitable tools exist.

Require the later reviewer to distinguish recomputed results from read-only review, check missed gouges, wrong centers, unsupported gasket segments, depth/assembly conflicts, unit errors, stale revisions, and unsafe material assumptions. Preserve accepted canon; proposed corrections require evidence and a recorded revision.

Keep the full private repository separate from a manufacturer package containing only necessary fabrication/reference data. Include file hashes, input/source hashes, code version, build parameters, and stale/superseded status. Record the source commit used for a build without creating a circular requirement that a manifest contain the hash of its own future commit.

## 14. First-run delivery and continuing work

On the first run, actually deliver as much of the following as the available inputs support:

1. Initialized/preserved Git repository, complete original ZIPs tracked directly in ordinary Git, verified input hashes and restoration, and a meaningful commit when identity/permissions allow.
2. Tested Blender/CadQuery setup and working project commands.
3. The wall-and-valve scan as the primary installed reference, a quality assessment of both plate scans, and a complete provisional assembly with uncertainty visible.
4. A saved, usable Blender scene and local HTML review with real project views.
5. The exact model-derived measurement worksheet and a short first batch of required readings.
6. Preliminary coverage/centering/gasket/depth checks and provisional design alternatives—not a fabricated declaration of fit.
7. A committed project checkpoint, documented remaining questions, and concise launch/rebuild instructions.

Do not claim completion of an artifact that failed to generate. If a file, software capability, or dimension is unavailable, state exactly what is missing, preserve the completed work, and continue tasks that do not depend on it.

When measurements arrive, validate IDs/units/revision, update the canon, rebuild, rerun dependent checks, refresh Blender and documents, and make an intelligible Git checkpoint. Explain material changes briefly. Do not require me to restate the project or approve ordinary reversible implementation decisions.

Before a fabrication-ready proposal, conduct an independent or fresh adversarial review of evidence, geometry, assembly, support, waterproofing assumptions, and export consistency. Use another reviewer only when actually available. Keep remaining uncertainties visible instead of hiding them behind a polished model.

Start now with the specified repository and three ZIPs. Preserve the sources first, then build the installation—not merely isolated plates.

## Primary-source starting points

Verify current APIs, instructions, and applicability. These references are not proof of the installed Kohler revision or approval of a retrofit.

- Blender documentation: https://docs.blender.org/manual/en/latest/
- Blender Python API: https://docs.blender.org/api/current/
- CadQuery installation: https://cadquery.readthedocs.io/en/latest/installation.html
- CadQuery exports: https://cadquery.readthedocs.io/en/latest/importexport.html
- Polycam exports: https://learn.poly.cam/hc/en-us/articles/27756102599572-What-File-Types-Can-Polycam-Export
- Polycam Object Mode: https://learn.poly.cam/hc/en-us/articles/27425185907348-How-to-Use-Object-Mode
- Optional FreeCAD: https://github.com/FreeCAD/FreeCAD
- Optional CloudCompare: https://www.cloudcompare.org/
- Optional Meshy: https://docs.meshy.ai/en/api/remesh
- Candidate Kohler stacked-trim guide: https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf
- Candidate oversized-plate supplier: https://designerdrains.com/product/oversized-escutcheon-plates/
- Example fabrication-file guidance: https://sendcutsend.com/guidelines/sheet-cutting/


## Confirmed component identities (user goal update, 2026-10-14)

- Large faceplate and two handles: K-T14489-4-BN, Purist MasterShower temperature and volume control trim.
- Small faceplate and one handle: K-T14491-4-BN, Purist MasterShower transfer/diverter trim.
- Main concealed valve: K-2973-KS-NA, MasterShower 1/2 inch thermostatic valve with integrated volume control and stops.
- Separate diverter purchased: K-737-K-NA, MasterShower 3/4 inch two-/three-way diverter. Purchase does not prove installed state.

This resolves the model leads above; dimensions remain nominal until physically checked.

2026-10-14 further goal correction: the K-737-K-NA is identified as the separate diverter valve, not merely a purchased item. Post-scan plumbing changes still unknown.
