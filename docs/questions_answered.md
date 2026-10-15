# Latest: does the aperture allow the knobs to attach?

The earlier diagonal aperture came from a buffered convex hull of selected scanned forward hardware. U/L points alone were not a handle-fit check. The separate [AP01 access study](../deliverables/current/fabrication/aperture-access/index.html) compares an upright 116.35 x 151.10 R33 opening with the old contour. It encloses the old aperture (minimum extra gap 0.446 mm), clears all 51,929 selected triangle projections, and reserves the entire measured 48.46 mm upper inner-opening footprint at its provisional placement with 11.0 mm extra margin. At the scan U center, nearest-edge distance rises from 11.3 to 35.9 mm. These are model clearances, not measured hub diameters or an accuracy bound.

Kohler 1041504-2-F pp. 7-8 shows the adapter/stem and front-plate hub connections; handle assemblies install from the front. They do not need their whole bodies fed through the custom backing plate. Rearward-reaching connection parts must remain clear at their actual depths, and correct adapters must still engage after the added outward shift. Hidden mating geometry and actual overlap remain unknown; the revised PDF states the thickness-correct dry-fit checks. Existing conditional upper-bare-tip rough-in concern remains open. Stud relief alone does not change U/L or valve depth.

The latest user confirmation establishes that the removed inner plate's foam meets its outer metal edge and the 4.56-inch rods meet the wood. Wood clearance holes are the authorized preferred approach if needed for retraction and other depth checks pass. The corrected rear drawing shows the foam reaching the edge; the existing F005 CAD already used that scenario. AP01 leaves nominal 1 mm extra metal inside an assumed uniform 6 mm band with R40 metal corners. Exact corners, local band width, alignment, compression and support still require checking. Historical statements below about wholly unknown outer-edge position or unconfirmed wood contact are superseded by this clarification.

# Questions answered at R001

These are conditional engineering observations, not physical fit or installation approval. Computations are in [checks.json](../deliverables/current/analysis/checks.json), registration in [registration.json](../deliverables/current/analysis/registration.json), and parameters in [resolved.json](../deliverables/current/analysis/resolved.json).

## Does an 8-inch plate cover the damage?

Not with a demonstrated error allowance. At the limiting traced feature CUT-03, an 8-inch circle has about 0.51 mm remaining in projection, before the 1.5 mm tracing allowance. Scale and positioning errors are still unknown. Individual margins are reported for OPEN-MAIN and CUT-01 through CUT-07; CUT-02/CUT-07 require visual confirmation. This is an inventory of visible/possibly visible damage, not certification that every physical defect was captured. The complete raw mesh remains available for challenge.

An 8-inch concentric plate around a nominal 7¼-inch trim adds **⅜ inch (9.525 mm) per side**. That visible border is different from intact-stone overlap. The 8¼-inch comparison adds ½ inch (12.7 mm) per side. The exploratory 230 mm outline provides about 13.91 mm at CUT-03 before tracing allowance, but its 10 mm trial land criterion has no released material/support basis.

## Where is the center?

The current trim center is inferred from the midpoint of the two observed tips, about X 0.80, Y 39.67 mm. It is distinct from the irregular opening centroid and diagonal stud midpoint. That is a placement hypothesis, not proof of real trim location. M06 derives the lower opening center from near/far edges and rim tangents; it can revise the trim relationship without moving the primary scan. Physical retention and repeatable centering are unresolved. The candidate has no added fastener holes because both stud paths fall inside its one aperture; that choice remains open to revision.

## Does the original gasket have support?

The assumed gasket path overlaps the opening. The current single rounded-rectangle candidate aperture also removes part of the assumed support footprint. Computed projected areas are diagnostic, since actual foam outline, notches, thickness and compression are unmeasured. The factory inner plate and gasket remain required. M02/M05 must replace the assumed path; width/height alone cannot establish continuous contact.

The new outer sealing band crosses GROUT-01. A planar CAD ring does not establish contact over the recess, adhesion to travertine, rigid support, or concealed waterproofing. Those functions are separate.

## Are the studs too long?

**October 15 source update:** Kohler's [1041507-5-F service diagram, printed page 9](https://resources.kohler.com/onlinecatalog/pdf/1041507_5.pdf#page=9) identifies 1038645 for the stacked two-control trim. The [manufacturer product specification](https://www.kohler.com/en/support/find-a-service-part/shop-parts/stud-10-24-x-4-56-l-1038645) is 10-24 × 4.56 in, or 115.824 mm nominal full length. This establishes the documented service part, not whether the installed rods are uncut originals. Under a perpendicular-to-tile assumption, current scan tips put rear ends about 89.2 mm (SW) / 85.1 mm (NE) behind tile; reaching the original 11.1 mm front limit would require about 15.5 / 19.6 mm inward travel. The wood plane is unmeasured. The rear photo supports surface contact but cannot exclude a shallow indentation/hole or resolve the second stud. [Review and calculation](../deliverables/current/review/rear/index.html#foam-and-studs).

The visible tip estimates are approximately 26.61 mm (SW) and 30.68 mm (NE) from the fitted stone plane at conditional scale. Kohler 1041504-2-F page 7 explicitly gives a 7/16-inch (11.1125 mm) maximum **from the finished wall**. The discrepancy warrants M07 straightedge measurements and a qualified check of actual adapters, threads, stud adjustment and final layer stack. It does not authorize cutting studs. The trial cover intersects both studs: signed rear-cover clearances are about -7.94 and -12.00 mm with the trial backing plate. This rejects the rendered assembly, while actual fit still needs measurements. See [the depth report](../deliverables/current/analysis/depth_stack.json).

The outer cavity, shell thickness, nuts, hubs, inner formed offsets and handle engagement are partly assumed. The manufacturer's exterior/BIM CAD cannot establish hidden mating details. No destructive adjustment or valve move is proposed.

## Which repair is preferable, and what materials are specified?

No option is selected. Reversible factory adjustment may fix seating but cannot restore missing gasket landing or cover remote saw cuts. Supported local rebuilding may restore land without increasing stack depth, if backing access, sound substrates and a compatible waterproofing connection exist. A custom plate could provide coverage, but currently lacks demonstrated gasket support, retention, stiffness, surface sealing and depth clearance. A combination may be viable. None requires additional tile cutting in the current scope.

No mortar, backing, sealant, metal alloy, finish, cure schedule or quantity is released. Products and purchasing sources will be checked against the selected interfaces; choosing them before substrate/access inspection would manufacture certainty. A draft fabricator inquiry is saved, not sent. No stock or local-code claims are made.

## Can the assembly be installed and serviced?

Not yet demonstrated. The layered model and sections expose likely conflicts, while [the draft manual](../deliverables/current/manual/index.html) retains hold points. A calibrated paper template checks planar coverage only. A thickness-accurate mockup must check seating, support, thread/handle engagement, drainage, removal paths and tools with the real parts.

The separate lower diverter now has a nominal 98.425 mm trim envelope centered at the captured visible tip, approximately (−0.07, −135.56, 42.25) mm. It is excluded from the registration fit. Center separation from the main trim is about 175.24 mm, leaving about 33.95 mm between nominal factory circles or 11.02 mm beside the 230 mm candidate. These are conditional projected gaps; actual center, diameter, placement and scale errors remain unbounded. See [the annotated neighbor view](../deliverables/current/review/views/neighbor_measure.png).

Kohler's 3-inch handle dimension is the axis-to-long-tip reach, not the total centered lever length. The reference handles now reflect that distinction. The main lower control and separate diverter have about 135.56 mm projected axis separation, compared with two 76.2 mm long reaches. Full-rotation reach circles overlap by about 16.84 mm. This flags an on-site travel/depth/tool-access check; it does not establish actual collision or that either handle permits every angle. Small-trim short reach is documented 31.75 mm; the main short reach and cross sections remain assumptions.

The **Original-wall trial** state removes the 4.175 mm trial plate/seal display stack from the main factory components. It retains original stone and captured hardware unchanged, with the lower diverter at the original wall plane. Both this state and the added-plate trial intersect the unchanged studs. They are labeled diagnostic conflicts, not manufacturer-intended fitted assemblies. Nuts and yellow plate clear the cover only in the assumed solids; the lower valve placeholder also clashes and needs real profile/bore evidence.

## What is physically verified?

Component identities were supplied by the user, who confirmed on 2026-10-14 that nothing has changed since capture. This current-state report is recorded separately from dimensions in `canon/observations.json`. No dimensional observations or fit-test results have been accepted. Local software checks establish evidence integrity, coordinate conversion and export consistency only. A successful render or CAD intersection test cannot establish water performance. [Dry-fit and incoming-inspection records](physical_checks/README.md) remain blank.

## Is the over-cut the only concern?

Not established. Concealing the cuts, supporting the foam/inner plate, resolving surface-water seals and drainage, and connecting concealed waterproofing are separate questions. The candidate does not yet provide demonstrated foam landing and its added depth changes seating and engagement. The [depth and sealing correction](decisions/depth_review_2026-10-14.md) explains the common datum and factory sequence.


## Could the valve or control adapters also be at the wrong depth?

Yes; that question is separate from stud length. The user confirms excessive stud projection and reports rear bolt contact with wood. The trim studs engage valve threads; rear wood anchorage is not their retaining mechanism. Check 09 now asks the installer to trace the same fasteners, distinguish structural framing from added blocking and establish usable rear travel/thread engagement. No cut/drill choice follows from the report.

The labeled K-2973-KS side-elevation dimensions place the upper bare tip 88.9 mm forward of the shower-outlet axis and the finished wall 61.9125–95.25 mm forward of that axis. Subtraction gives a nominal bare-upper-tip projection of −6.35 to +26.9875 mm from tile. The current scan estimate is about +31.95 mm. This is a conditional flag of about 4.97 mm beyond the nominal maximum only if the same bare tip is being compared. An attached adapter, revision mismatch, valve tilt or scan error can invalidate that comparison. No lower-stem or separate-diverter limit is inferred.

Check 10 records as-found upper/lower tip identity and separate block/gap readings. The import preserves signed projection and classifies it as a diagnostic cross-check. Those readings do not silently relocate the scan or CAD valve. A physically confirmed depth still needs the plaster-guard or manufacturer-axis check, correct adapter/screw selection, full handle/bonnet and cover seating, operation and drainage at the final layer thickness. See `deliverables/current/analysis/depth_stack.json` and [the preserved inquiry](physical_checks/depth_inquiry_2026-10-14.json).

Internal valve seals contain supply water. The wall plane is not a seal against the bare stem. Incorrect trim depth can compromise seating and protection against exterior water entry; it does not by itself diagnose a damaged cartridge seal. These remain separate tests. Sources: preserved `kohler-1041504_2.pdf` pp3,7–8; `kohler-2973-KS-spec.pdf` p3; `kohler-2973-install-1205551-2.pdf` pp10–13,25.

## Actual outer-cover measurements (R005)

The outward-facing cover has a user-measured diameter of 7.25 inches (184.15 mm), corroborating the nominal size, and an upper inside opening of 33.79 mm. On 2026-10-15 the user confirmed 46.25 mm between the nearest inside opening edges, and 35.23 mm from the lower opening bottom inside edge to the bottommost outside rim. Both gaps are accepted in R005; neither is a center distance. For aligned openings, center spacing is 63.145 mm plus half the unmeasured lower bore diameter. The baseline diagnostic model retains a 36 mm lower-bore display placeholder; F005 uses a separate equal-bore hypothesis of 33.79 mm, giving conditional 80.04 mm centers. Neither lower-bore value is accepted. F005 geometry is unchanged because its prior scenario used the now-confirmed edge contacts. The loose-cover photograph does not set installed Z depth or prove rear clearance, gasket compression or water performance. See `docs/physical_checks/outer_plate_contacts_2026-10-15.json`; Check 12 requests the independent lower diameter and Check 06-C measures both local rear clearances.
