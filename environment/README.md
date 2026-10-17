# Tested local environment and restoration

This project was built on macOS arm64 with Blender 4.5.13 LTS and isolated Python 3.12.14 / CadQuery 2.8.0. Exact observed versions are in `tested_versions.json`; tested Python dependencies are in `requirements.lock`. The browser's Three.js modules and license are vendored, with package metadata in `three-package.json`. No CAD packages are installed into Blender's Python.

The existing Blender application was reused. In this Codex session, native Blender needs the ordinary macOS process environment outside the filesystem sandbox; sandbox startup crashed. CPU renders succeeded without security-setting changes. From a normal local terminal, use the wrapper directly. Set `PROJECT_BLENDER` if Blender is installed elsewhere.

For a laptop checkout and viewing only (Python 3 required):

```sh
git clone https://github.com/mdpatrick/shower-kohler-valve.git
cd shower-kohler-valve
./project validate --git-objects
./project review
```

These two project commands use the Python standard library. They do not need Blender, CadQuery, `uv`, a virtual environment or regenerated meshes. `review` opens FT02; the RF03 print guide is at `http://127.0.0.1:8765/fabrication/FT02/formwork-print/index.html`. The current PDFs, videos, print ZIP and packed Blender snapshots are already saved in the checkout. GitHub's web interface does not execute the HTML review; use the local launcher.

All four original Polycam ZIPs and the selected outputs are ordinary Git blobs. A full clone includes project history. Use `git pull --ff-only` for later committed updates. Local browser/session logs, private vendor account exports, extracted copies, build caches and virtual environments are deliberately excluded. No `user_notes.blend` existed at the October 17 transfer checkpoint. See the [transfer scope](../docs/decisions/github_transfer_2026-10-17.json).

For optional rebuilding, first install/reuse `uv`, Python 3.12 and a compatible Blender application. From the cloned repository:

```sh
git fsck --full
PROJECT_PYTHON=/path/to/python3.12 ./scripts/setup.sh
./project ingest
./project build
./project validate --git-objects
./project review
```

A self-contained local bundle is an alternative clone source: `git clone /path/to/shower-kohler-valve.git.bundle shower-kohler-valve-restored`. A bundle must be copied elsewhere to serve as an off-machine backup.

`scripts/setup.sh` uses an existing `uv` executable and a Python 3.12 interpreter, creates only `.venv`, and installs the lock file's binary packages. On this machine the tested interpreter is `/Users/mdpatrick/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`. It does not replace system Python or install applications. A new machine needs a compatible Blender installation and the fonts used by the PDF generator (`Arial.ttf` and `Arial Bold.ttf` under the macOS supplemental fonts directory, or an explicit source adaptation).

No Downloads paths are used after initial copy. `ingest` checks repository ZIP hashes and safely extracts OBJ/MTL/texture relationships. `build` caches per-stage input/output hashes in ignored `build/stages.json`. Canon is input, never a build output. Changed generated files are preserved before regeneration. A source commit plus source-tree hash avoids a manifest depending on its own future commit.

`build` reconstructs the base evidence using the current measurement revision, then dispatches applicable historical reference stages and the selected FT02 parts, Blender views, documents and audit. These earlier stages recreate ignored reference meshes needed by the current stage. Use `prepare-fit-trial` for a targeted current-design rebuild after that initial preparation. RF03 is separate: run `prepare-form-print --stage cad`, then `capture`, `render`, `documents` and `audit`; see START_HERE. Saved outputs can be viewed without running any of these stages.

`scripts/verify_restore.py --bundle <path> --rebuild --report <receipt.json>` is the older local recovery harness. Its additional STL comparison targets the historical FT01 folder; do not describe it as an RF03 rebuild check. The current manifest and `./project validate --git-objects` verify the selected saved outputs. Keep a recovery receipt outside the bundle it verifies.

The historical AP01 audit checks accepted evidence against its original checkpoint. A generated REAR01 Blender file is checked against its hash immediately before AP01 runs; a later standalone audit checks the last successful preservation receipt. Rebuilding Blender can change serialization without changing the source meshes, so historical `.blend` byte identity is not required after an authorized regeneration. REAR01 separately verifies source mesh geometry, UVs and placement after saving and reopening.

The [FT01 recovery receipt](../docs/validation/restore_current_FT01_2026-10-15.json) records the initial audit failure and the corrected continuation in the same isolated checkout. All six current STL geometries and all 15 rendered handoff pages matched the saved versions; accepted canon and the frozen GP01 package stayed unchanged. Resolved dimensional fields are compared exactly. Copied observation text must match current accepted canon, with additions/removals/updates listed separately. The restored model legitimately includes two later qualitative observations absent from the older resolved snapshot.

`review` binds to `127.0.0.1:8765`, checks that the project page responds, then opens it. Use `PROJECT_REVIEW_PORT=8766 ./project review` for another port. The page has no CDN dependency. File-only opening retains static content, but browser security may prevent module/GLB loading; use the local launcher for interactive 3D.

Developer checks:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python src/cad/coordinate_test.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python src/blender/coordinate_test.py
node tests/browser_review.mjs
```

The coordinate test produces a known 100 × 60 × 4 mm solid, an offset 10 mm hole, and a clipped northeast corner. The browser test uses a separate temporary Chrome context; synthetic readings never enter canon. Set `PROJECT_PLAYWRIGHT` to an installed Playwright module and `PROJECT_REVIEW_URL` when needed. Browser test tools are optional for ordinary viewing/building.

The selected `.blend` is deliberately self-contained with packed textures. Auxiliary raw inspection renders can be regenerated by `src/blender/inspect_scans.py` after ingestion; they are not required to rebuild CAD. Selected secondary-scan assessment views stay in the versioned review snapshot.

`./project handoff` makes a full `--all` Git bundle, verifies it and preserves tracked/untracked nonignored work separately if the repository is dirty. A separate ignored `user_notes.blend` is included in that timestamped uncommitted-files ZIP when present. It also writes an analysis review ZIP containing annotated views, computations, measurement instructions, the draft dependency sequence and the applicable public trim guides. Nothing is automatically transmitted. Do not treat the compact review ZIP as the full evidence backup.
