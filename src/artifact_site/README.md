# Hosted project artifact hub

Site: https://shower-kohler-artifacts.mdpatrick.chatgpt.site

This is the owner-private ChatGPT Site for the current project handoffs. The Site ID is preserved in [.openai/hosting.json](.openai/hosting.json); **reuse it on every update**. Do not create another Site or change its audience without an owner request.

## Content and reproducibility

Run from the project root:

```sh
python3 scripts/prepare_artifact_site.py
python3 -m http.server 8772 --bind 127.0.0.1 --directory build/sites/shower-artifacts/dist
```

The first command creates a dedicated ignored checkout under `build/sites/shower-artifacts`. It copies the current FT02 tree, the saved interactive references and their local dependencies, three original Polycam ZIPs and the input manifest. Larger files are linked to the GitHub commit recorded at build time. Push all changed source artifacts to GitHub before publishing a snapshot that references them.

`catalog.json` selects the 35 handoff entries shown in the library. `index.html`, `site.css` and `site.js` implement the hub. The complete hosted inventory is generated as `artifact-manifest.json` with input hashes, file sizes, hosted versus GitHub storage and the source commit. Hosted page navigation/links are adapted; original project HTML remains unchanged. CAD, documents, images, videos and ZIPs are copied byte for byte.

The dedicated Site source contains `web/`, a hash-pinned `assets.json` recipe and `hydrate_assets.mjs`; generated `dist/` is ignored there. Running `node hydrate_assets.mjs` in that checkout reconstructs the exact static output from the committed pages and pinned GitHub originals. An optional `--cache /absolute/path/to/previous/dist` avoids downloading unchanged files; cached bytes must pass the same size and SHA-256 checks. The deployment archive includes the actual binary assets even though the Site source Git history does not duplicate them. The engineering GitHub repository still stores the original files directly, without LFS.

The largest hosted asset is below the [25 MiB static-file limit](https://developers.cloudflare.com/workers/platform/limits/). Three large Blender scenes and the primary wall Polycam download from GitHub. No original ZIP is split or repacked. The Site does not include browser sessions, credentials, private vendor account exports, environments or extracted caches.

## Publishing with the Sites plugin

Use the Sites skill and its source helper, preserving the ID in this directory’s hosting manifest. Use the dedicated checkout above, not the engineering repository root. Supply a fresh source credential through the helper’s hidden standard input; never save it in this repository or put it in command arguments.

On this Mac, `/usr/local/bin/git` is an older Apple Git without the helper’s required `--config-env` option. Select the already-installed Git 2.50.1 from `/Applications/Xcode.app/Contents/Developer/usr/bin` in the helper process’s PATH. No global Git changes are needed.

Package the checked static Site with `site-workflow.mjs`, using `commands: [["node", "hydrate_assets.mjs"]]` (optionally with `--cache`) and an absolute `archivePath`. Skip the hydration command only when the identical output has already been verified and inputs are unchanged. Publish the helper’s exact returned `commit_sha` and archive with `save_version_and_deploy_private`. The engineering repository and the Site source have separate Git histories; the engineering history and original scans remain in `mdpatrick/shower-kohler-valve`.

Check the desktop/mobile layout, search/category filters, print ZIP download, current document pages and local link closure. Record deployment success and identifiers in `docs/validation/artifact_site_2026-10-17.json`, then update/push the project README. The native successful deployment response verifies publication. The saved browser checks describe the local preview, not an authenticated production-browser test.

## Scope

RF03 is the current temporary print form. FT02 / R006 is the selected plain main/diverter plate pair for quote and sacrificial dry fit, with clear and metal alternatives. TR03/RF02, TR02 and older tools remain labeled studies. Publication does not change geometry, accepted measurements, purchase authorization or physical installation readiness.
