#!/usr/bin/env python3
"""Build the artifact hub without changing engineering deliverables."""
from pathlib import Path
from html import escape, unescape
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from urllib.parse import quote, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/artifact_site'
CURRENT = ROOT / 'deliverables/current'
FT = 'fabrication/FT02/'
MAX_ASSET = 25 * 1024 * 1024
REPO_URL = 'https://github.com/mdpatrick/shower-kohler-valve'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', default='build/sites/shower-artifacts')
    args = parser.parse_args()
    checkout = (ROOT / args.checkout).resolve()
    if not checkout.is_relative_to(ROOT / 'build/sites'):
        raise SystemExit('Use a dedicated ignored build/sites checkout.')
    checkout.mkdir(parents=True, exist_ok=True)
    hosting = json.loads((SOURCE / '.openai/hosting.json').read_text())
    sharing = json.loads((SOURCE / 'sharing.json').read_text())
    assert sharing['project_id'] == hosting['project_id']
    existing = checkout / '.openai/hosting.json'
    if existing.exists() and json.loads(existing.read_text()).get('project_id') != hosting['project_id']:
        raise SystemExit('Refusing to change the identity of an existing Site.')
    existing.parent.mkdir(exist_ok=True)
    existing.write_text(json.dumps(hosting, indent=2) + '\n')
    dist = checkout / 'dist'
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    tracked = {ROOT / p for p in subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT, text=True).split('\0') if p}
    selected = {p for p in tracked if p.is_relative_to(CURRENT / 'fabrication/FT02') or p.is_relative_to(CURRENT / 'visualizations') or p.is_relative_to(ROOT / 'data/raw/polycam')}
    selected.add(ROOT / 'canon/inputs.json')

    def local_url(path):
        if path.is_relative_to(CURRENT):
            return '/artifacts/' + path.relative_to(CURRENT).as_posix()
        if path.is_relative_to(ROOT / 'data/raw/polycam'):
            return '/originals/' + path.name
        if path == ROOT / 'canon/inputs.json':
            return '/originals/inputs.json'
        raise ValueError(path)

    def github_url(path, download=True):
        rel = quote(path.relative_to(ROOT).as_posix(), safe='/')
        if download:
            return f'https://raw.githubusercontent.com/mdpatrick/shower-kohler-valve/{commit}/{rel}'
        return f'{REPO_URL}/blob/{commit}/{rel}'

    # Include local page dependencies, including images assigned by embedded JS.
    quoted = re.compile(r'''["']([^"'<>\s]+\.(?:html|png|jpe?g|webp|svg|pdf|css|js|mp4|srt|json|txt|zip|step|stl|3mf|blend)(?:[?#][^"'<>\s]*)?)["']''', re.I)
    inspected = set()
    while True:
        pending = [p for p in selected if p.suffix.lower() in ('.html', '.css', '.js') and p not in inspected]
        if not pending:
            break
        for path in pending:
            inspected.add(path)
            for match in quoted.finditer(path.read_text()):
                url = urlsplit(unescape(match.group(1)))
                if url.scheme or url.netloc or url.path.startswith('/'):
                    continue
                dependency = (path.parent / unquote(url.path)).resolve()
                if dependency in tracked and dependency.is_relative_to(CURRENT):
                    selected.add(dependency)

    copied = {p for p in selected if p.stat().st_size <= MAX_ASSET}
    def url_for(path):
        return local_url(path) if path in copied else github_url(path)

    assets = []
    rewritten = []
    for path in sorted(selected):
        target_url = url_for(path)
        entry = dict(repository_path=path.relative_to(ROOT).as_posix(), url=target_url,
                     bytes=path.stat().st_size, sha256=digest(path),
                     storage='Site' if path in copied else 'GitHub',
                     role='original scan' if path.suffix == '.zip' and 'polycam' in path.parts else 'project artifact')
        if path in copied:
            dest = dist / target_url.lstrip('/')
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() in ('.html', '.css', '.js'):
                text = path.read_text()
                def replace(match):
                    old = unescape(match.group(1))
                    parsed = urlsplit(old)
                    if parsed.scheme or parsed.netloc or parsed.path.startswith('/'):
                        return match.group(0)
                    dependency = (path.parent / unquote(parsed.path)).resolve()
                    if dependency not in selected:
                        return match.group(0)
                    new = url_for(dependency)
                    if parsed.query:
                        new += '?' + parsed.query
                    if parsed.fragment:
                        new += '#' + parsed.fragment
                    return match.group(0)[0] + new + match.group(0)[-1]
                text = quoted.sub(replace, text)
                if path.suffix.lower() == '.html':
                    nav = '<div style="font:14px/1.5 system-ui;padding:12px 20px;background:#102f3c;color:white"><a style="color:white" href="/">← Project artifact hub</a> · Saved project document · Current PS01 print selection: BOTH relieved 24 mm forms are primary; short D12 is optional. Earlier default labels are historical.</div>'
                    if re.search(r'<body\b[^>]*>', text, re.I):
                        text = re.sub(r'(<body\b[^>]*>)', lambda m:m.group(0) + nav, text, count=1, flags=re.I)
                    elif '<main' in text:
                        text = text.replace('<main', nav + '<main', 1)
                    else:
                        text += nav
                dest.write_text(text)
                if digest(dest) != entry['sha256']:
                    rewritten.append(entry['repository_path'])
                entry['hosted_sha256'] = digest(dest)
            else:
                shutil.copyfile(path, dest)
                assert digest(dest) == entry['sha256'], path
        assets.append(entry)

    catalog = json.loads((SOURCE / 'catalog.json').read_text())
    rows = []
    for item in catalog:
        path = ROOT / item['path']
        if path not in selected:
            raise ValueError('Unpackaged catalog artifact: ' + item['path'])
        item = dict(item, url=url_for(path), storage='Site' if path in copied else 'GitHub', size_mb=round(path.stat().st_size/1e6, 2))
        rows.append(item)
    (dist / 'catalog.json').write_text(json.dumps(rows, indent=2) + '\n')
    provenance = dict(project_id=hosting['project_id'], artifact_source_commit=commit,
                      source_repository=REPO_URL, date='2026-10-17',
                      scope='Current FT02 files, RF03 and RF04 print packages, TR03/RF02 and TR02 studies, FIN01, archived interactives and original Polycam archives.',
                      audience=sharing['audience'], max_static_asset_bytes=MAX_ASSET,
                      asset_limit_source='https://developers.cloudflare.com/workers/platform/limits/',
                      oversized_downloads='Original bytes linked to the already-pushed GitHub commit. No splitting or repacking of source ZIPs.',
                      page_adaptations='Only hosted HTML/JS/CSS links and hub navigation are adapted; original engineering deliverables are unchanged.',
                      rewritten_pages=rewritten, files=assets)
    (dist / 'artifact-manifest.json').write_text(json.dumps(provenance, indent=2) + '\n')
    for name in ('index.html', 'site.css', 'site.js', 'sharing.json'):
        shutil.copyfile(SOURCE / name, dist / name)
    (dist / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    (dist / '404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Artifact not found</title><h1>Artifact not found</h1><p><a href="/">Return to the artifact hub</a></p></html>')
    hosted_bytes = sum(p.stat().st_size for p in dist.rglob('*') if p.is_file())
    report = dict(project_id=hosting['project_id'], checkout_path=str(checkout),
                  artifact_source_commit=commit, hosted_files=len(copied), linked_large_files=len(selected-copied),
                  total_site_bytes=hosted_bytes, original_binary_hashes_verified=True)
    (checkout / 'BUILD_RECORD.json').write_text(json.dumps(report, indent=2) + '\n')
    # The Site source repository holds pages plus a pinned asset recipe. Large
    # generated output is packaged for deployment, not duplicated in Git history.
    web = checkout / 'web'
    if web.exists():
        shutil.rmtree(web)
    web.mkdir()
    text_types = {'.html', '.css', '.js', '.json', '.txt', '.srt', '.md'}
    source_by_url = {entry['url'].lstrip('/'): entry for entry in assets if entry['storage'] == 'Site'}
    binary_assets = []
    for file in sorted(dist.rglob('*')):
        if not file.is_file():
            continue
        rel = file.relative_to(dist)
        if file.suffix.lower() in text_types:
            target = web / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
        else:
            entry = source_by_url[rel.as_posix()]
            binary_assets.append(dict(path=rel.as_posix(), bytes=file.stat().st_size,
                                      sha256=digest(file), source_url=github_url(ROOT / entry['repository_path'])))
    (checkout / 'assets.json').write_text(json.dumps(binary_assets, indent=2) + '\n')
    (checkout / '.gitignore').write_text('dist/\n')
    shutil.copyfile(SOURCE / 'hydrate_assets.mjs', checkout / 'hydrate_assets.mjs')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
