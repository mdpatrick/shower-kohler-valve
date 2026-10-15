# F005 fabrication preparation

Public primary-source research only. No geometry uploaded, no vendor contacted, no quote obtained, no order placed.

## Current fit findings
- Mounting pattern: conditional 112.05 mm versus scan tip distance 108.010 mm. No physical fit declared.
- Forward scan: 51929 clipped triangles; zero conflicts with new aperture.
- Rear foam path remains decisive: 1.5 mm inset can erase model landing.
- Unchanged studs interfere with assumed cover. No cutting/drilling/relocation specified.
- The measured outer-cover inside-edge/equal-bore scenario gives 80.04 mm centers.

## Costs and vendor evidence
USD planning allowances for one main plate plus one matching diverter plate, quantity one each. Ranges are assistant estimates, not published part prices or vendor quotes. No tax, shipping upgrade, installation, primer/sealant or separate cosmetic finishing included unless noted. Exact vendor totals require a later authorized quote using the chosen geometry and finish.

### SendCutSend - Clear acrylic laser prototype, 3.0 mm
Planning pair allowance $40-100 (not a quote).
No price for this pair. Pricing depends on material, geometry, quantity and processing; published free US shipping threshold is $39.
Standard sheet cutting ships in 2-4 business days. 0.118 inch acrylic appears on rush eligibility list; 24-hour production is conditional on checkout eligibility and noon PT cutoff.
Keep protective film; verify actual thickness. Prototype only; add a measured 0.175 mm spacer to imitate the 3.175 mm metal stack, if needed.
- https://sendcutsend.com/materials/
- https://sendcutsend.com/pricing/
- https://sendcutsend.com/sendcutsend-processing-times/

### Ponoko - Clear acrylic laser prototype, stock near 3 mm
Planning pair allowance $50-130 (not a quote).
Advertises acrylic parts from $50 for one; that is a starting offer, not a price for these plates.
Advertises same-day production/delivery options. Rush order cutoff 11 AM; same-day local Bay Area or next-day mainland-US options are conditional. Confirm material, destination and current cart date.
Clear acrylic exposes the foam landing and valve interference during dry fit. Custom non-stock materials add fees/delay, so use standard stock.
- https://www.ponoko.com/laser-cutting/acrylic
- https://www.ponoko.com/laser-cutting
- https://help.ponoko.com/en/articles/4468203-custom-material-orders

### 3D Printer on Demand - FDM plastic dry-fit pair
Planning pair allowance $40-120 (not a quote).
No fixed design price. Vendor states no tooling, setup fee or minimum order on its rapid-prototyping page.
Published typical production/ship lead time 3-5 business days; transit additional.
PLA/PETG published instant-pricing size limit 250 mm; 230 mm plate fits that stated envelope. Ask for a single flat print, no scaling, and thickness/flatness inspection. Thin wide prints can warp. Published domestic shipping $7.95 per order, additional to the planning range.
- https://www.3dprinterondemand.com/use-cases/rapid-prototyping
- https://3dprinterondemand.com/
- https://3dprinterondemand.com/pricing

### Xometry - Industrial FDM plastic prototype pair
Planning pair allowance $100-300 (not a quote).
Design-specific quote required; reserve range is an assistant budget, not a published vendor rate.
US 3D-printing page advertises 1-day FDM expedites. Standard and actual delivery date depend on geometry/material/capacity; eligible domestic 3D printing has free 2-day or ground shipping.
Use only if a confirmed expedited date justifies its quote. Check flatness, thickness and print orientation; a smooth appearance alone does not establish fit.
- https://www.xometry.com/capabilities/3d-printing-service/
- https://community.xometry.com/kb/articles/651-how-much-is-shipping
- https://community.xometry.com/kb/articles/642-what-is-your-minimum-order-quantity

### SendCutSend - 316 stainless laser pair, 0.060 or 0.125 inch
Planning pair allowance $65-180 (not a quote).
No part-specific price. Published material options include 0.060 and 0.125 inch; laser tolerance +/-0.005 inch (0.127 mm).
Standard ships in 2-4 business days; deburring adds 0 days, detabbing +1 day. The current 316 rush list contains 0.187 and 0.250 inch ONLY, so do not assume 24-hour service for these thin plates.
Request deburring and tab removal. Raw/deburred stainless is not Kohler BN. Reserve an additional $50-150 and 2-5 business days for separate cosmetic brushing only as an unquoted planning contingency.
- https://sendcutsend.com/materials/stainless-steel-316/
- https://sendcutsend.com/sendcutsend-processing-times/
- https://sendcutsend.com/pricing/

### OSH Cut - 304 #4 brushed stainless 0.060 inch, or 316 #2B 0.060 inch
Planning pair allowance $75-220 (not a quote).
No geometry-specific price. Official materials list includes 304 #4 brushed with protective film and 316 #2B in 0.060 inch. No minimum order amount advertised.
Standard laser-cut prototype/short-run lead time 2 business days; same-day options depend on job size, stock and capacity. Confirm extra time for selected finishing and transit.
304 #4 stock offers the simpler cosmetic route. 316 has greater chloride resistance but its listed #2B surface is not a matching brush. Deburring/graining offered; request finish protection, grain direction and edge treatment.
- https://www.oshcut.com/
- https://www.oshcut.com/services/deburring

### Ponoko - 304 stainless laser-cut pair
Planning pair allowance $90-250 (not a quote).
No part-specific price obtained; material page confirms 304 options.
Current service page advertises same-day cutting; verify stock/finish eligibility. Do not use the older 2019 blog's 15-day lead time as today's quote.
Ask for stock thickness matching the chosen STEP and a protected cosmetic surface. Quoted alloy, finish, tolerance and delivered date must be reconciled before release.
- https://www.ponoko.com/laser-cutting/stainless-steel
- https://www.ponoko.com/sheet-metal-fabrication

## Rebuild
Run `./project prepare-fabrication`. Canon is read-only input. Reconcile evidence revision before changing manufacturing geometry.

## Release checks
Rear foam trace; stud/cover/adapter fit; supported on-wall prototype and control travel; alloy/thickness/finish and explicit manufacturing release.
