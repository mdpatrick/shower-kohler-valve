# Shower / Kohler escutcheon project

**[Open the hosted artifact hub →](https://shower-kohler-artifacts.mdpatrick.chatgpt.site)**

Browse the current print package, plate CAD, installer PDFs, narrated video, design studies and original Polycam downloads without running a local server. The owner made the ChatGPT Site public to anyone with the link on October 17, 2026. A reminder is set for October 24 to restore owner-only access; it does not change access automatically. The GitHub files below remain available separately.

For a friend helping with the print, start with [Why we’re printing this](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/#repair-context): the over-cut wall photo beside the proposed main/diverter escutcheon mockup, with a short explanation of the temporary form’s role.

Quick links: [MASV downloads with images and dimensions](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/#print) · [both relieved-collar sizes](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/formwork-small-bed/index.html) · [current illustrated print guide](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/selected-forms/SEND_TO_PRINTER/PRINT_THIS_GUIDE.pdf) · [current print ZIP](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/selected-forms/SELECTED_DEEP_FORMS_AND_OPTIONAL_SHORT.zip) · [installer PDF](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/PLUMBER_START_HERE.pdf) · [search all handoffs](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/#library).

**Current plates: FT02 / R006. Selected print forms: BOTH deeper relieved versions (RF03 Ø240 + RF04 Ø192.55). The short 12 mm collar is optional only.** Start with [START_HERE.md](START_HERE.md) for the selected designs, installation context and unresolved physical checks.

This repository preserves the complete project history, all five original Polycam ZIPs, supplied photos, manufacturer references, accepted measurements, CAD sources, Blender scenes, videos and handoff documents. Original ZIP bytes are stored directly in ordinary Git; Git LFS is not used.

Public MASV downloads prioritize **original deep RF03 (Ø240 × 32 mm)** and **small deep RF04 (Ø192.55 × 32 mm)**. Both have 24 mm maximum relieved collars. The current combined handoff also includes a separately labeled optional short D12 backup. Each link allows 25 download attempts and was set to expire October 27, 2026. The Site also retains a direct ZIP backup. See the [current sharing record](docs/decisions/selected_forms_sharing_2026-10-17.json).

**Latest evidence — October 19:** [FS01: three installation scans versus calipers](deliverables/current/analysis/formwork-scan-FS01/index.html), including the newly printed form as an independent calibration reference. The new source ZIP and separate Blender inspection are preserved. The report recommends retaining the current slots and trying small removable locators before another full tighter print; no new form is released.

## Open on another computer

```sh
git clone https://github.com/mdpatrick/shower-kohler-valve.git
cd shower-kohler-valve
./project review
```

Viewing the saved browser review needs Python 3.9 or newer, but no CAD installation or rebuild. The launcher opens the local FT02 review at `http://127.0.0.1:8765/fabrication/FT02/index.html`. Open the latest print guide at `http://127.0.0.1:8765/fabrication/FT02/formwork-print/index.html`. PDFs and the print ZIP can also be opened directly from the checkout. After cloning, the saved review works offline.

Use [environment/README.md](environment/README.md) for validation, optional rebuilding and the tested software versions. The GitHub repository was public when checked on October 17, 2026. The owner explicitly requested this repository upload, including Polycams and recent artifacts; see the [transfer record](docs/decisions/github_transfer_2026-10-17.json).

The [GitHub recovery check](docs/validation/github_remote_restore_2026-10-17.json) verified a full remote clone, all four original ZIPs, 588 saved artifacts and the review launcher under Apple Python 3.9.6 without a virtual environment.

## Files to use

| Purpose | Current artifact |
|---|---|
| Both relieved-collar sizes: original + small bed | [RF04_ORIGINAL_AND_SMALL_BED_PRINT_PACKAGE.zip](deliverables/current/fabrication/FT02/formwork-small-bed/RF04_ORIGINAL_AND_SMALL_BED_PRINT_PACKAGE.zip) |
| RF04 comparison and print guide | [View online](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/formwork-small-bed/index.html) · [PDF](deliverables/current/fabrication/FT02/formwork-small-bed/SEND_TO_PRINTER/PRINT_GUIDE.pdf) |
| Original D12 + relieved D24 print package | [RF03_FRIEND_PRINT_PACKAGE.zip](deliverables/current/fabrication/FT02/formwork-print/RF03_FRIEND_PRINT_PACKAGE.zip) |
| RF03 illustrated guide and cost estimate | [View online](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/formwork-print/index.html) · [saved HTML](deliverables/current/fabrication/FT02/formwork-print/index.html) |
| Current plate designs and installer handoff | [FT02 online review](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/index.html) · [saved HTML](deliverables/current/fabrication/FT02/index.html) |
| Clear acrylic trial pair | [FT02_CLEAR_FIT_TRIAL.zip](deliverables/current/fabrication/FT02/FT02_CLEAR_FIT_TRIAL.zip) |
| Alternative stainless trial pair | [FT02_METAL_FIT_TRIAL.zip](deliverables/current/fabrication/FT02/FT02_METAL_FIT_TRIAL.zip) |
| Installer's starting document | [PLUMBER_START_HERE.pdf](deliverables/current/fabrication/FT02/PLUMBER_START_HERE.pdf) |
| Actual scan, proposed appearance and exploded assembly | [FT02 Blender scene](deliverables/current/fabrication/FT02/escutcheon_fit_trial_FT02.blend) |
| Smaller-slot and deeper-collar studies | [TR03 / RF02 online](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/tab-refinement/index.html) · [saved HTML](deliverables/current/fabrication/FT02/tab-refinement/index.html) |
| Narrated explanation using both scans | [TR02 video page](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/tab-rethink/index.html) · [saved video](deliverables/current/fabrication/FT02/tab-rethink/TR02_tabs_foam_and_two_scans_NARRATED.mp4) |
| Finish comparison on captured travertine | [FIN01 online](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/fabrication/FT02/finish-study/index.html) · [saved HTML](deliverables/current/fabrication/FT02/finish-study/index.html) |
| Earlier interactive measurement and tab explanations | [Hosted visualization archive](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifacts/visualizations/index.html) · [saved HTML](deliverables/current/visualizations/index.html) |
| Original scans and hash manifest | [data/raw/polycam](data/raw/polycam) and [canon/inputs.json](canon/inputs.json) |

RF04 adds a smaller Ø192.55 mm face to the relieved 24 mm-collar form: allow 203 × 203 mm usable bed including brim. It keeps the same collar, tabs and slots while reducing minimum outer face overhang by half. The combined ZIP preserves the original Ø240 relieved form too. Print at 100%; select one size and one file format. The smaller face guides less repair area and still needs independent padded support.

RF03 is a temporary, removable repair tool. Its default file has a 12 mm collar and smaller locating slots; print one form, choosing the optional relieved 24 mm version only if needed. FT02 remains the separate plain-aperture main/diverter pair for quotes and sacrificial dry fit. A print file or successful software check does not establish physical fit or permanent waterproof installation.

Older FT01, F005, CB01, AP01 and GPT Pro packages remain available as history. Generated measurement illustrations are archived references and do not override accepted R006 calipers. Do not send a historical whole-shower STEP assembly as a plate manufacturing file.

```sh
./project validate --git-objects   # original bytes and saved artifact checks
./project query dimension main.outer_diameter_mm
./project query solid MAIN        # selected plate; CAD dependencies required
./project handoff                 # optional local Git bundle and review ZIP
```

Regenerable extracts, build caches, virtual environments, browser session data and private account exports stay local. Source, accepted evidence and selected outputs are included. The full project scope is preserved in [docs/project_request.md](docs/project_request.md).

## Updating the hosted hub

The Site hosts the current project artifacts and a searchable handoff library, including both RF04/RF03 relieved-collar print sizes. Four larger originals are linked to the preserved GitHub revision because static assets are limited to 25 MiB per file. The [hosted manifest](https://shower-kohler-artifacts.mdpatrick.chatgpt.site/artifact-manifest.json) records each file’s source path, hash and storage location. CAD, PDF, ZIP, scan and video bytes are unchanged; only the hosted page links/navigation are adapted.

The reproducible Site source is in [src/artifact_site](src/artifact_site), with the build command and publication workflow in its [maintenance guide](src/artifact_site/README.md). See the [publication and verification record](docs/validation/artifact_site_2026-10-17.json). This is a dated snapshot; rebuilding engineering files locally does not automatically publish them.
