# Verified Kohler shower parts

Research date: 2026-10-14 (America/Los_Angeles). Documentation revision: PARTS-R001.

Status: **DRAFT_NOT_FOR_FABRICATION** — component identity and purchase evidence only.

This list records models verified from order correspondence and retailer SKU matches. The four core control components are also identified in the current [project request](project_request.md#confirmed-component-identities-user-goal-update-2026-10-14) and [project state](../canon/project_state.json). Documentary verification does not establish physical dimensions, installed revision, fit, or water performance. **BN means Vibrant Brushed Nickel.**

## Parts

- **K-T14489-4-BN — Kohler Purist large faceplate and two-handle MasterShower temperature/volume trim.** Exact SKU in [SupplyHouse order 29063740][S1], dated October 5, 2026. Identified as existing trim in the [October 14 custom-plate request][S3] and in the current project identity record.
- **K-T14491-4-BN — Kohler Purist small faceplate and single-handle MasterShower transfer/diverter trim.** Exact SKU in [SupplyHouse order 28850707][S2], dated September 18, 2026. Identified as existing trim in the [October 14 custom-plate request][S3] and in the current project identity record.
- **K-2973-KS-NA — Kohler MasterShower 1/2-inch thermostatic valve with integrated volume control and stops.** The [September 18 Home Depot order WN70958610][S4] lists SKU **1001483799**, which [Home Depot maps to this model][M1]. Identified as the main concealed valve in the current project identity record.
- **K-737-K-NA — Kohler MasterShower 3/4-inch two- or three-way diverter valve.** Exact SKU in [SupplyHouse order 28850707][S2]. The [Home Depot order][S4] also lists SKU **1002459928**, which [maps to this model][M2]. The current project request records a later user correction explicitly identifying this as the separate diverter valve. Preserve the duplicate-purchase and return-label history described below.
- **K-13688-G-BN — Kohler Contemporary Round 8-inch rainhead, 1.75 GPM.** Exact SKU in [SupplyHouse order 28850707][S2]. Purchase confirmed; installation not independently verified.
- **K-10124-BN — Kohler wall-mounted rainhead arm and flange.** Exact SKU in [SupplyHouse order 28850707][S2]. Purchase confirmed; installation not independently verified.
- **K-9660-BN — Kohler Persona 1/2-inch × 1/2-inch vacuum breaker.** Exact SKU in [SupplyHouse order 28850707][S2]. Purchase confirmed; installation not independently verified.
- **K-22166-G-BN — Kohler Purist three-spray handheld showerhead, 1.75 GPM.** [Home Depot order][S4] SKU **1003991938**; [retailer model/SKU match][M3] shows **22166-G-BN** (without Kohler's optional K- prefix). Purchase confirmed; installation not independently verified.
- **K-98342-BN — Kohler Awaken 24-inch deluxe slide bar.** [Home Depot order][S4] SKU **1000112650**; [retailer model/SKU match][M4]. Purchase confirmed; installation not independently verified.
- **K-9514-BN — Kohler MasterShower 60-inch metal shower hose.** [Home Depot order][S4] SKU **1007185821**; [retailer model/SKU match][M5]. Purchase confirmed; installation not independently verified.
- **K-22172-BN — Kohler Purist/Stillness wall-mounted supply elbow with check valve.** [Home Depot order][S4] SKU **1003993989**; [retailer model/SKU match][M6]. Purchase confirmed; installation not independently verified.

Inch sizes and flow rates above are product names, nominal sizes, or ratings. They are not measurements accepted into the project's millimeter-based canon.

## Identity and purchase history

The earlier chat/project lead **K-T14489-4** was initially unverified. The October 5 SupplyHouse receipt establishes the exact purchased model and finish **K-T14489-4-BN**, and the October 14 correspondence names it as existing trim. That evidence supports identity, not dimensional or installation approval.

The K-737-K-NA diverter appears in both September 18 orders. An [October 5 Home Depot email][S5] issued a return label for the diverter from order WN70958610, with a November 4 return deadline. A return label does not prove a completed return or identify which purchased unit was installed. The separate SupplyHouse purchase remains documented.

Earlier research therefore described the diverter only as purchase-confirmed. The latest October 14 user-goal correction preserved in [project_request.md](project_request.md) explicitly identifies **K-737-K-NA as the separate diverter valve, not merely a purchased item**; [project_state.json](../canon/project_state.json) includes all four core models in `confirmed_component_ids`. Retain that later user identification alongside the order/return evidence. Post-scan piping configuration, installed revision, particular-unit provenance, and physical dimensions remain unresolved.

A [RetroFlow Plumbing invoice for October 5 service][S7] describes replacement with a new Kohler unit and copper piping, but gives no Kohler model. It supports the reported work description; it does not assign an exact model to visible or concealed hardware, establish the complete present piping arrangement, or record a leak test.

## Source context and limits

- **S1:** SupplyHouse confirmation **29063740**, October 5, 2026, forwarded in business email. Establishes the main trim's exact SKU and finish.
- **S2:** SupplyHouse confirmation **28850707**, September 18, 2026, forwarded as “SHOWER PARTS.” Establishes the small trim, diverter, rainhead, shower arm/flange, and vacuum-breaker SKUs.
- **S3:** “Custom Escutcheon Plate Request: Two Circular Backing Plates,” October 14, 2026. Names the two existing trims. Its proposed custom-plate dimensions are not accepted measurements or approved fabrication dimensions.
- **S4:** Home Depot confirmation **WN70958610**, September 18, 2026. Establishes purchased item descriptions and retailer SKUs; M1–M6 supply the exact model crosswalks.
- **S5:** Home Depot return-label email, October 5, 2026. Establishes initiation of the diverter return only.
- **S6:** [September 18 Slack fixture-plan message][S6], with `Kohler_Shower_Fixture_Plan_Updated_Open_Wall.pdf`. Useful planning context, subordinate to actual receipts and later identity updates. A suggested item or alternative in that plan is not proof of purchase or installation.
- **S7:** RetroFlow Plumbing invoice **1088**, emailed October 13, for October 5 service. Work description lacks component model numbers.
- **M1–M6:** Public Home Depot model/SKU listings linked from the part bullets. The four accessory matches M3–M6 were checked on October 14, 2026. Retailer Q&A/review-page headers were used for their model/SKU fields, not customer statements.
- Manufacturer specifications, installation guides, and reference CAD already saved by the reconstruction work are indexed separately in [canon/source_register.json](../canon/source_register.json). Their nominal geometry and revision applicability must still be checked against the installation.

Email and Slack links require the user's account access. This document preserves a sourced transcription of the relevant identities, not a complete archive of the emails. No billing address, payment details, or unrelated correspondence is reproduced.

## What this does not establish

- These are assembly/product model numbers. Subsequent October 15 manufacturer research identifies **1038645 trim studs** and **1035854 seal/front-plate assembly** in the stacked two-control drawing, printed page 9 of [1041507-5-F](https://resources.kohler.com/onlinecatalog/pdf/1041507_5.pdf#page=9). The [stud product page](https://www.kohler.com/en/support/find-a-service-part/shop-parts/stud-10-24-x-4-56-l-1038645) specifies 10-24 × 4.56 in. This does not establish that the installed rods are uncut originals. Other service-part identities and revision applicability still require their own evidence. See [the research record](physical_checks/foam_and_stud_research_2026-10-15.json).
- Oversized backing plates are proposed custom pieces with no Kohler model number. No custom diameter, aperture, thickness, material, or fabrication tolerance is selected or approved by this document.
- Physical dimensions, installation/clearance checks, gasket support, waterproofing, fabrication approval, and installed leak testing are not completed by receipt or model verification. Preserve the travertine and factory plate, gasket, drainage, and service functions.
- This documentation adds provenance; it does not modify the canon, accepted measurements, reconstruction geometry, selected repair, or readiness flags.

## Verification record

**Documentary review performed:** read the relevant Gmail/Superhuman receipts and repair correspondence; matched Home Depot item SKUs to public model listings; reviewed the Slack plan, prior chat context, and current repository identity updates. Findings are separated above into purchased identities, reported existing trim, later user identification, and remaining unknowns.

**Physical tests performed for this research:** none. No on-site measurement, fit, installation, waterproofing, or leak-test result is claimed.

[S1]: https://mail.superhuman.com/search/kohler%20/thread/1a10d7a693288e6b
[S2]: https://mail.superhuman.com/search/kohler%20/thread/1a0b70cebc87fe9c
[S3]: https://mail.superhuman.com/search/kohler%20/thread/1a13c10ee218a6a1
[S4]: https://mail.google.com/mail/u/0/#search/kohler/WhctKLcMdBQLbSKvNSKldcwnNmZGRZFCNTrfsnmCLhfMCntPBZRgdzSxzttBtTFjXJlvxcg
[S5]: https://mail.google.com/mail/u/0/#search/kohler/WhctKLcMgCpGSKpfNXcwhHcZGhtrFlbNdBKkqvvXjMpMWHTNPLcSqLhcqwfXVkxKnfXwDTB
[S6]: https://foundmyfitness.slack.com/archives/C0B32AJQ9FY/p1789764256552909?thread_ts=1789764256.552909&cid=C0B32AJQ9FY
[S7]: https://mail.google.com/mail/u/0/#search/kohler/WhctKLcMgDvLHMgXcfPRtxkMRVDgKFDkkCxdwTxGNrwxwhcTtXMXbVQphLvncxlDnFbGHtg
[M1]: https://www.homedepot.com/p/KOHLER-MasterShower-1-2-in-Thermostatic-Valve-with-Integrated-Volume-Control-and-Stops-K-2973-KS-NA/203782796
[M2]: https://www.homedepot.com/p/203782860
[M3]: https://www.homedepot.com/p/reviews/KOHLER-Purist-3-Spray-Wall-Mount-Handheld-Shower-Head-1-75-GPM-in-Vibrant-Brushed-Nickel-22166-G-BN/309502423/1
[M4]: https://www.homedepot.com/p/reviews/KOHLER-Awaken-24-in-Deluxe-Slide-Bar-in-Vibrant-Brushed-Nickel-K-98342-BN/205178699/1
[M5]: https://www.homedepot.com/p/questions/KOHLER-MasterShower-60-in-Metal-Shower-Hose-in-Vibrant-Brushed-Nickel-K-9514-BN/100065658/1
[M6]: https://www.homedepot.com/p/questions/KOHLER-Purist-Stillness-Wall-Mount-Supply-Elbow-with-Check-Valve-in-Vibrant-Brushed-Nickel-K-22172-BN/315769796/1
