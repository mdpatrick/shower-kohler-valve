# Seated-cover visualization rejected

The user correctly flagged the `assembled.png` depiction at checkpoint `dbaa438`: unchanged captured studs protruded through a decorative cover drawn in its seated position. The cover has no bolt/nut passages. Labeling the scene merely "proposed" and putting the already-computed clashes lower in the review was misleading.

No physical readings accompanied the comment. The source scan, original landmarks, transform, stud positions, candidate geometry and accepted measurement revision remain unchanged. No stud cutting, valve movement, new outer-cover holes or deeper cavity has been invented to make the image fit.

The two former assembly views are now explicitly diagnostic **Original-wall trial** and **Trial fit conflict**. The raw images carry the failure warning; red stud envelopes expose the conflicts. They are not a manufacturer-intended fitted assembly. The guide establishes the intended sequence, but the real mating profiles and installed dimensions remain unresolved.

## Recomputed depth relationships

`./project query depth` returns exact analytic cover/axis intersections, whole-part Z ranges, and exact OCCT solid intersections for both display cases. All Z values use the fitted original intact-stone plane. Values below are conditional model values, not physical readings.

| At stud | Unchanged tip Z | Cover rear, original wall | Cover rear, trial plate | Signed gap with trial plate |
|---|---:|---:|---:|---:|
| SW | 26.61 mm | 14.50 mm | 18.675 mm | -7.94 mm |
| NE | 30.68 mm | 14.50 mm | 18.675 mm | -12.00 mm |

The simplified nut and inner-plate solids do not intersect the cover. Their actual shape, seats, washers/stops, formed depth and compressed gasket spacing remain unknown. The lower valve envelope also intersects the cover; its collar profile and cover bore are assumptions, so this is a reconstruction conflict, not a newly established physical defect. Cover/part Z-range overlap alone is not used as collision proof: X/Y topology matters.

The trial landing plane shifts by 4.175 mm: 3.175 mm plate plus a 1 mm illustrative seal layer. The foam is shown at its assumed **free** 3 mm thickness. Neither installed compression nor a sealant specification follows from those spacers. The custom aperture is open at the stud axes; the custom plate is not solid in those axial paths.

## Verified manufacturer meaning

Re-read and visually inspected preserved Kohler `1041504-2-F` page 7 and current `1216755-2-A` steps 8–12 against their official online versions. The older guide explicitly states a maximum stud projection of 7/16 inch **from the finished wall**. The earlier generic "confirm datum" wording was unnecessarily ambiguous. This is not a cut length, and translating the limit outward above a custom plate would require review of the new assembly, not automatic manufacturer approval.

The guide sequence is studs into valve, inner plate over studs and flat at the wall, nuts behind the decorative cover, cover drain downward, and handles retaining the cover through the inner-plate hubs. The foam must cover the wall opening. Page 8 connects correct adapter length with engagement and cover seating. Check the actual installed revision.

## Water performance is not a coverage result

The review distinguishes concealed saw marks, rigid support/continuous foam landing, surface-water seals/drainage, and concealed waterproofing continuity. The current candidate also has an assumed gasket/aperture conflict and is not selected. A scan or cover render cannot establish a hidden membrane connection or diagnose whether a prior leak came from supply/valve plumbing or surface water.

Prioritize existing Checks 04–07 and installer Check 09. Record each stud's local rear-cover cavity separately in Check 06 notes. No new numerical readings were accepted; existing R001 response files remain compatible.
