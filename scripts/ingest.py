"""Byte-preserving initial copy and reproducible, defensive local extraction."""
from pathlib import Path, PurePosixPath
import argparse, datetime, hashlib, json, os, shutil, stat, zipfile, zlib

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['shower-hole-valve-polycam.zip', 'plates-side-1-polycam.zip', 'plates-side-2-polycam.zip']

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def members(z):
    out=[]; seen=set()
    for i in z.infolist():
        p=PurePosixPath(i.filename)
        mode=i.external_attr>>16
        if (p.is_absolute() or '..' in p.parts or '\\' in i.filename or ':' in i.filename
            or not p.parts or i.filename in seen or stat.S_ISLNK(mode)
            or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR))):
            raise ValueError(f'Unsafe/duplicate archive entry: {i.filename}')
        seen.add(i.filename)
        if i.file_size > 2_000_000_000: raise ValueError('Unexpectedly large input member')
        out.append({'name':i.filename,'size_bytes':i.file_size,'compressed_bytes':i.compress_size,
                    'zip_timestamp_raw':list(i.date_time),'crc32':f'{i.CRC:08x}'})
    return out

def cached_member_ok(path,entry,root):
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):return False
    if not path.is_file() or path.stat().st_size!=entry['size_bytes']:return False
    crc=0
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):crc=zlib.crc32(chunk,crc)
    return f'{crc:08x}'==entry['crc32']

def ingest(source_dir=None):
    dest=ROOT/'data/raw/polycam'; dest.mkdir(parents=True,exist_ok=True)
    mp=ROOT/'canon/inputs.json'
    old=json.loads(mp.read_text()) if mp.exists() else None
    entries=[]
    for index,name in enumerate(NAMES):
        target=dest/name
        source=Path(source_dir).expanduser()/name if source_dir else None
        if source:
            h=sha(source); n=source.stat().st_size
            if target.exists() and sha(target)!=h:
                target=dest/(source.stem+'__sha256_'+h[:16]+'.zip')
            if not target.exists(): shutil.copy2(source,target)
            assert sha(target)==h and target.stat().st_size==n
        elif not target.exists():
            raise FileNotFoundError(f'Missing preserved input {target.relative_to(ROOT)}')
        h=sha(target)
        with zipfile.ZipFile(target) as z:
            inventory=members(z)
            required=sum(i['size_bytes'] for i in inventory)
            if shutil.disk_usage(ROOT).free < required*2: raise OSError('Insufficient extraction space')
            extracted=ROOT/'data/extracted'/target.stem
            if extracted.is_symlink():raise ValueError('Extraction root must not be a symlink')
            stamp=extracted/'.input-sha256'
            reuse=stamp.exists() and stamp.read_text().strip()==h and all(
                cached_member_ok(extracted/i['name'],i,extracted)
                for i in inventory if not i['name'].endswith('/'))
            if not reuse:
                extracted.mkdir(parents=True,exist_ok=True)
                for i in z.infolist():
                    p=extracted/i.filename
                    if p.is_symlink() or not p.resolve().is_relative_to(extracted.resolve()):
                        raise ValueError('Extraction target escapes or is a symlink')
                    if i.is_dir(): p.mkdir(parents=True,exist_ok=True); continue
                    p.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(i) as a,open(p,'wb') as b: shutil.copyfileobj(a,b)
                stamp.write_text(h+'\n')
        entry={'id':['SCAN-WALL','SCAN-PLATE-1','SCAN-PLATE-2'][index],
            'source_path':str(source) if source else None,'repository_path':str(target.relative_to(ROOT)),
            'sha256':h,'size_bytes':target.stat().st_size,
            'role':'primary installed spatial reference' if index==0 else 'secondary component reference',
            'user_quality_assessment':'best and most accurate of supplied scans' if index==0 else 'looks distorted; reflective metal suspected',
            'calibrated_accuracy_mm':None,'capture_date':None,
            'export_name_date':'2026-10-14 (filename only; not established capture date)',
            'filesystem_mtime_utc':datetime.datetime.fromtimestamp(target.stat().st_mtime,datetime.timezone.utc).isoformat(),
            'timestamp_note':'ZIP member date 1980-01-00 is invalid and not capture evidence.',
            'archive_members':inventory,'extraction_path':str(extracted.relative_to(ROOT))}
        entries.append(entry)
        print(name,entry['size_bytes'],h,'extraction reused' if reuse else 'extracted')
    if old and not source_dir:
        for a,b in zip(old['inputs'],entries):
            assert a['sha256']==b['sha256'] and a['size_bytes']==b['size_bytes'], 'Preserved evidence changed'
    else:
        mp.parent.mkdir(parents=True,exist_ok=True)
        mp.write_text(json.dumps({'project_id':'shower-kohler-valve','schema_version':1,'inputs':entries},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source-dir'); args=p.parse_args(); ingest(args.source_dir)
