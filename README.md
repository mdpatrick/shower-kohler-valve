# Shower / Kohler escutcheon project

**Current plates: FT02 / R006. Latest temporary print form: RF03.** Start with [START_HERE.md](START_HERE.md) for the selected designs, installation context and unresolved physical checks.

This repository preserves the complete project history, all four original Polycam ZIPs, supplied photos, manufacturer references, accepted measurements, CAD sources, Blender scenes, videos and handoff documents. Original ZIP bytes are stored directly in ordinary Git; Git LFS is not used.

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
| Hand directly to a friend for 3D printing | [RF03_FRIEND_PRINT_PACKAGE.zip](deliverables/current/fabrication/FT02/formwork-print/RF03_FRIEND_PRINT_PACKAGE.zip) |
| RF03 illustrated guide and cost estimate | [Formwork print guide](deliverables/current/fabrication/FT02/formwork-print/index.html) |
| Current plate designs and installer handoff | [FT02 review](deliverables/current/fabrication/FT02/index.html) |
| Clear acrylic trial pair | [FT02_CLEAR_FIT_TRIAL.zip](deliverables/current/fabrication/FT02/FT02_CLEAR_FIT_TRIAL.zip) |
| Alternative stainless trial pair | [FT02_METAL_FIT_TRIAL.zip](deliverables/current/fabrication/FT02/FT02_METAL_FIT_TRIAL.zip) |
| Installer's starting document | [PLUMBER_START_HERE.pdf](deliverables/current/fabrication/FT02/PLUMBER_START_HERE.pdf) |
| Actual scan, proposed appearance and exploded assembly | [FT02 Blender scene](deliverables/current/fabrication/FT02/escutcheon_fit_trial_FT02.blend) |
| Smaller-slot and deeper-collar studies | [TR03 / RF02](deliverables/current/fabrication/FT02/tab-refinement/index.html) |
| Narrated explanation using both scans | [TR02 video page](deliverables/current/fabrication/FT02/tab-rethink/index.html) |
| Finish comparison on captured travertine | [FIN01](deliverables/current/fabrication/FT02/finish-study/index.html) |
| Earlier interactive measurement and tab explanations | [Portable visualization archive](deliverables/current/visualizations/index.html) |
| Original scans and hash manifest | [data/raw/polycam](data/raw/polycam) and [canon/inputs.json](canon/inputs.json) |

RF03 is a temporary, removable repair tool. Its default file has a 12 mm collar and smaller locating slots; print one form, choosing the optional relieved 24 mm version only if needed. FT02 remains the separate plain-aperture main/diverter pair for quotes and sacrificial dry fit. A print file or successful software check does not establish physical fit or permanent waterproof installation.

Older FT01, F005, CB01, AP01 and GPT Pro packages remain available as history. Generated measurement illustrations are archived references and do not override accepted R006 calipers. Do not send a historical whole-shower STEP assembly as a plate manufacturing file.

```sh
./project validate --git-objects   # original bytes and saved artifact checks
./project query dimension main.outer_diameter_mm
./project query solid MAIN        # selected plate; CAD dependencies required
./project handoff                 # optional local Git bundle and review ZIP
```

Regenerable extracts, build caches, virtual environments, browser session data and private account exports stay local. Source, accepted evidence and selected outputs are included. The full project scope is preserved in [docs/project_request.md](docs/project_request.md).
