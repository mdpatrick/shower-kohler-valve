# FT01 quote request — prepared, not sent

15 October 2026. This replaces the earlier inquiry for a 230 mm / 3.175 mm study. The current request is for **one main backing and one diverter backing** as a sacrificial fit trial. The owner has not authorized sending this inquiry, uploading files or placing an order. Fabrication of a trial does not release it for permanent installation.

Use the relevant text below with the current custom-only files. Enter the actual delivery destination and needed arrival date when requesting a quote. Request a total for the pair, not a per-part headline price. No installation photographs, scans or private review package are needed by the cutting/printing vendor.

## Metal shop — copyable request

Please quote one each of these two flat custom backing plates, revision FT01, in millimeters:

| Part | Outside profile | Through opening | Quantity |
| --- | --- | --- | --- |
| FT01_MAIN_220_T1524_FIT_TRIAL | Circle, diameter 220 mm | Centered upright capsule, 116.35 mm wide × 151.10 mm high; semicircular ends R58.175 mm; straight sides 34.75 mm | 1 |
| FT01_DIV_124_T1524_FIT_TRIAL | Circle, diameter 124 mm | Concentric circle, diameter 80 mm | 1 |

Both parts are **1.524 mm / 0.060 inch thick**. Please price 316 stainless with deburring and directional satin graining, and separately quote a lower-cost 304 brushed-stock alternative if available. State the alloy, actual stock thickness and thickness range; do not substitute another gauge or scale the profiles without identifying the change. A different thickness changes the installed fit.

There are no bolt holes, tabs, threads, countersinks, bends or embossing. These are sheet-cut profiles; metal additive printing is unnecessary. Please use the supplied STEP or DXF as the cutting geometry. The two-page shop drawing gives dimensions and notes; it is not a second set of cutting paths.

Requested targets are profile ±0.13 mm and overall free-state flatness within 0.50 mm after finishing. Please confirm whether those targets are achievable and included in your quote, and identify any proposed exception. Report actual finished thickness and how flatness is checked. These are requested targets, not assumed shop guarantees.

Deburr both faces and all internal and external edges, remove cutting microtabs and heat tint, and provide smooth edges safe to handle. Maintain the specified opening profiles. Use a consistent directional satin grain on both parts and state the grain direction, process and finish designation. Identify the visible face and protect it for shipping. Please distinguish a raw cut surface, deburring, graining, and protected brushed stock in the price. Exact matching to Kohler brushed nickel is not required or presumed; a finish sample or representative photo would help the owner choose.

Please return:

- Price for the two parts, material option, setup/minimum charges, deburring and decorative finishing, inspection, packaging, shipping and applicable tax, with a delivered total.
- Quote validity, stock availability, production lead time **including finishing**, estimated ship date and transit separately; any rush option and its full added cost.
- Any geometry or manufacturability concern, requested revision, thickness substitution or tolerance exception before work starts.
- Whether an inspection record of outside/opening sizes, thickness and flatness is included or available at added cost.
- Remake/reorder price for the same pair after a possible fit-trial revision, if different from the first-order price.

Delivery destination: [enter when sending]. Needed arrival date: [enter when sending, or ask for earliest practical arrival].

This is a request for a quote, not an order. The first pair is a fit trial and may need revision. The installer will establish support, retention, gasket contact, handle engagement and sealing on site; no claim is made that these parts alone waterproof the installation.

## Plastic or acrylic shop — copyable request

Please quote the same FT01 pair above, quantity one each, as a physical fit trial. Compare the following separately where your process supports them:

1. **Thickness-matched printed pair:** T1524 STL files, 1.524 mm thick, one diameter-220 main and one diameter-124 diverter. Units are mm. Please recommend a practical plastic and print orientation for a flat, solid fit template, state expected warping and actual finished thickness, and confirm the entire main part fits your build area without splitting. Do not rescale the model or add thickness without identifying the change.
2. **3 mm alternative:** T3000 STL for printing, or T3000 DXF with explicitly selected 3 mm clear acrylic for sheet cutting. Same planar dimensions. This is a separate alternative, **not another pair to order**. It adds 1.476 mm more depth than the metal design, so it cannot by itself prove the 1.524 mm metal stack fits.

Requested plastic profile target is ±0.25 mm and free-state flatness within 0.50 mm. State what your process can actually deliver, including hole/profile accuracy, actual thickness, support removal, edge treatment and finish. The part must be handleable without sharp edges. No permanent wet-area material approval is being requested; this trial checks shape, access, contact and the stated thickness only. It does not qualify stainless stiffness or a water seal.

Please give the delivered total for the pair with all setup, finishing, inspection, shipping and tax; expected ready-to-ship date and transit separately; rush cost; and the cost/time of a possible revised pair. Delivery destination and needed arrival date will be supplied with the quote request. This is not an order.

## Files and comparison

The current [T1524 quote ZIP](../../deliverables/current/fabrication/fit-trial/FT01_recommended_T1524_quote.zip) contains both parts' STEP, DXF and STL files, shop drawings, notes and hashes. The [T3000 alternative ZIP](../../deliverables/current/fabrication/fit-trial/FT01_plastic_T3000_quote.zip) is separate. Upload **one format per part** appropriate to the process; the different formats describe the same part, not additional quantities. Verify the preview shows 220 mm and 124 mm outside diameters. STL does not encode an authoritative unit choice; select mm explicitly.

The diameter-120 / diameter-80 diverter is a separate fallback for a tight installed neighbor gap. Its files are in the [CAD folder](../../deliverables/current/fabrication/fit-trial/cad); they are not an extra default item in either pair ZIP. Ask for a separate fallback price only if useful, and identify which diverter will actually be ordered.

Compare **like-for-like delivered pair totals and arrival dates**. The owner's preference is to consider finished metal as the first trial when its delivered total is about twice plastic or less and it arrives in time, accepting possible remake cost. A quoted plastic thickness change, omitted metal finishing or rush/transit difference must remain visible in that comparison. Vendor replies, quote numbers and expiry dates should be saved before any purchase decision. Public lead times and budgeting allowances in the guide are not actual quotes.

Keep received quotes separate from the field-fit record. Choosing a price/material route does not mark the physical fit, support/seal design or permanent-installation checks complete. After any dimensions or material change, reconcile the quote against `canon/fit_trial_design.json` and regenerate affected files before ordering.
