# Shower escutcheon project — start here

**FT01 is the current recommendation for a quote and sacrificial physical fit trial.** Permanent installation has not been released. No upload, purchase or physical fit test has occurred. Accepted measurement evidence remains R005; older studies are retained as history.

Open the [current illustrated review](deliverables/current/fabrication/fit-trial/index.html), or run `./project review`. The review includes individual upload files, prices and timing research, paired mockups, an exploded view, and the actual new scan with the inner plate attached.

The [GP01 Pro review package](deliverables/current/gpt-pro-review/GP01/GPT_PRO_PROMPT_PACKAGE_GP01.zip) is ready. Follow its `00_READ_ME_FIRST.txt`: attach the brief, visual evidence and technical archive, then paste the master prompt. It requests independent design review and concrete instructions back to the agent for CAD, optional locators and separate party-specific handoffs. No Pro response has been received. GP01 is a frozen review checkpoint; later software maintenance has not changed the nominal FT01 design.

## Choose the next part

- Main: Ø220 mm, centered vertical capsule opening 116.35 × 151.10 mm, semicircular ends R58.175.
- Diverter: Ø124 / Ø80 mm; separate Ø120 fallback if the two installed backing plates are too close.
- First quote: 1.524 mm / 0.060 inch stainless, deburred and directionally grained. Compare 316 with 304 brushed stock. Matching STL supports a thickness-matched plastic print. A 3 mm plastic/acrylic alternative changes the depth stack by another 1.476 mm.
- No fixed bolt tabs. Both rods and factory connection openings sit inside one broad access opening. Center on the actual covers and verify retention without forcing the factory nuts.
- Prefer metal as the first fit trial if the finished, delivered price is about twice plastic or less and timing works. Accept possible remake cost. No actual vendor quote has been obtained.

[Recommended pair quote ZIP](deliverables/current/fabrication/fit-trial/FT01_recommended_T1524_quote.zip) · [3 mm alternative ZIP](deliverables/current/fabrication/fit-trial/FT01_plastic_T3000_quote.zip). Each ZIP contains only its two custom parts, drawings, shop notes and hashes. Send a vendor individual STEP/DXF for sheet cutting or STL for printing. All units are mm; order one main and one diverter, one thickness.

## Bring to the Kohler expert

[Seven-page project handoff](deliverables/current/fabrication/fit-trial/project_handoff_FT01.pdf) · [dimensioned shop sheets](deliverables/current/fabrication/fit-trial/shop_drawings_FT01.pdf) · [A3 100% templates](deliverables/current/fabrication/fit-trial/full_size_templates_FT01.pdf) · [three-scene Blender file](deliverables/current/fabrication/fit-trial/escutcheon_fit_trial_FT01.blend).

[Fillable expert visit record](deliverables/current/fabrication/fit-trial/expert_visit_record_FT01.pdf): four pages for incoming inspection, factory attachment, complete-stack fit, and the actual repair/cure/tests. Save a dated copy and attach referenced photos; all 75 fields are blank or NOT RECORDED. It also has a matching blank JSON and field dictionary. See [record instructions](docs/physical_checks/README.md). The current full-size paper template is **two A3 sheets**, not the historical four-sheet set.

The expert should establish factory handle engagement first, address the confirmed rod/wood obstruction if necessary, then trial the complete stack and both plates together. Check all foam contact, support, retention, cover seating, handle operation, service removal and bottom drainage. Record the chosen support/seal system and cure before permanent installation; test plumbing leaks separately from shower spray ingress. The fillable record preserves observations for reconciliation; completing it does not automatically approve a design. No additional homeowner measuring campaign is required to obtain quotes.

## Evidence and actual limits

Physical calipers govern loose-part dimensions. The original wall/valve scan remains the primary spatial reference, unchanged. The supplemental [attached-inner-plate scan](data/raw/polycam/polycam-inner-plate-attached.zip) is preserved, extracted and visually assessed separately. In wall-normal projection its stems appear about 3–4 mm high in visible hub rings; reflective geometry and a roughly 4 mm width discrepancy prevent precision inference. It is not globally registered to the primary scan and does not prove engagement. [Assessment](deliverables/current/fabrication/fit-trial/attached_scan_assessment.json).

FT01 clears 51,929 scoped primary captured surface pieces in each of three earlier placement hypotheses, with minimum projected clearance about 1.6 mm. The aperture leaves only 1 mm nominal extra land inside the assumed 6 mm foam. Neither is a verified field tolerance. Diverter rear contact geometry, real foam footprint/compression, support stiffness and hidden interfaces remain physical checks. [Design report](deliverables/current/fabrication/fit-trial/design_report.json) · [fresh export/analytic audit](deliverables/current/fabrication/fit-trial/audit.json).

The user confirms the foam belongs to the inner plate, reaches its outer edge, and the 4.56 inch trim rods touch wood. Wood clearance behind those rods is the preferred conditional remedy if the remaining valve/handle depths pass. No wood drill dimensions are established. Preserve travertine: no tile cutting, grinding, drilling or enlargement. Retain factory plate, gasket, drainage and service functions.

## Rebuild and maintain

`canon/fit_trial_design.json` is the dimensional input. `canon/fit_trial_handoff.json` holds editable guide prose and research. `./project prepare-fit-trial` rebuilds stale analysis, Blender, documents and audit stages. Use `--stage analysis|blender|documents|audit` for a targeted stage or `--force` to rebuild it. Blender requires the documented unsandboxed desktop launch on this Mac. Start a restored checkout with `./project ingest` and `./project build` to recreate ignored prerequisite meshes. The current scene embeds the supplemental scan; CAD remains the authority for custom parts.

Record real checks in `docs/physical_checks/` against FT01, preserve source evidence, revise dimensions with reasons and rebuild all dependent outputs. Run `./project validate --git-objects` for original archive and project checks. Use ordinary Git; no LFS or external upload. Local Git/bundles are not an off-machine backup.

`./project query` now defaults to the current FT01 design. Examples: `dimension main.outer_diameter_mm`, `dimension stocks.0.thickness_mm`, `solid MAIN`, `solid DIV T3000`, `coverage CUT-03`, `clearance`, `depth`, and `compare-states`. Exact solid queries reimport the current STEP; coverage recomputes the current outer-circle margins to the stored main-damage traces in all three unselected poses. Clearance reads the saved, source-hash-checked report and says so. Unknown installed depth values remain null. Use `./project query historical ...` for the older R005 reconstruction, factory reference solids and rejected assemblies. Default `features`/`measure` remain explicitly labeled evidence-registry queries; `section`/`reconcile-centers` remain historical diagnostics. Derived current results refuse stale source/report files. `candidate.diameter_mm` and `solid CUSTOM-01` are compatibility aliases for the current main plate, not the old 230 mm candidate.

Design-dependent guide text uses `[[name:format]]` tokens resolved by `src/fabrication/fit_trial_spec.py`; keep measured facts and dated vendor evidence distinct from these design values. The helper checks the current centered capsule/ring family and stock identities. A different shape needs an explicit builder change. Run `.venv/bin/python -m unittest tests.test_fit_trial_parameters -v` after changing dimension propagation: it generates an unpublished variant under `build/` and checks actual CAD and PDF profiles, labels, HTML and shop packages without changing the selected dimensions. See [validation](docs/validation/parameter_propagation_FT01.json). The A3 layout currently rejects outside diameters above 230 mm rather than silently clipping them.

[Complete continuing goal](docs/fabrication_goal_prompt.md) · [review instructions](docs/downstream_audit_prompt.md) · [original request](docs/project_request.md) · [historical studies and earlier starting page](START_HERE_history_pre_FT01.md).
