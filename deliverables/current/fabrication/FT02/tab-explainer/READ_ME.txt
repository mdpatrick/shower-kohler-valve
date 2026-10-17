FT02 — why the bolt tabs were not selected

Play FT02_tabs_and_foam_explained.mp4. It is a 36-second captioned video.
The optional FT02_tab_explanation.blend contains the animated geometry and packed scan texture.
This folder is an explanation, not a package to send for manufacture.

TIMELINE
0–5 s: the amber round-hole/slot tabs added to the blue custom plate.
5–17 s: the plate approaches the original captured rod end.
17–22 s: a close-up of the small source-surface overlap near the seated upper-right tab.
22–31 s: nominal foam backing, then an illustrative sideways shift.
31–36 s: the selected plain FT02 plate, without tabs.

WHAT THE MOVIE DOES AND DOES NOT ESTABLISH
The plate and tabs come from CadQuery solids. The original wall/valve capture uses
its unchanged recorded transform. The tab layout comes from the accepted coplanar
inner-plate survey; its pose against the installed capture remains an approximation.
Installed tip-to-tip distances are 3D and were not used as planar hole coordinates.
The captured rod end is an obstruction along this modeled insertion path. Removing
or retracting the rods could remove that end obstruction. The small seated overlap
remains scan/placement evidence, not a proven physical defect or certified error.

The foam example is a LOCAL STRAIGHT-EDGE section, with 6 mm nominal width and
6 mm free depth. The foam belongs to the factory inner plate, hidden in this close-up.
The 7 mm nominal inset provides the complete 6 mm band plus 1 mm extra inward backing.
Illustrative relative shift: (7.00−4.826)/2 + (5.66−4.826)/2 = 1.504 mm.
The 4.826 mm crest is a thread nominal, not an owner measurement. This is a conservative
clearance opportunity, not measured motion: the second locator and clamping constrain it.
At a 1.504 mm shift, 0.504 mm of this nominal foam band extends beyond the backing edge.
That is not a leak threshold or a full-perimeter contact prediction.

The selected plain plate still needs correct centering, firm support and factory clamping.
The removable front border gauge is a positioning aid, not a permanent fastener.
Physical fit, actual gasket contact, handle engagement and water performance remain untested.

REBUILD FROM THE REPOSITORY
./project explain-tabs --stage all
Optional: --stage preview for seven review frames. Build caches are under build/FT02/tab_explainer.
provenance.json records input hashes, geometry and the numerical illustration.
No selected plate manufacturing geometry or vendor package was changed by this explanation.
