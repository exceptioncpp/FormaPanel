#!/usr/bin/env python3
"""Safe inventory of manufacturer ZIP archives; lists only file names/sizes (no extraction).

This intentionally never prints file contents, since vendor code may contain embedded secrets.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def scan(path: Path) -> dict:
    if not path.is_file(): raise FileNotFoundError(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    with ZipFile(path) as z:
        items = [{'path': i.filename, 'uncompressed_bytes': i.file_size, 'compressed_bytes': i.compress_size}
                 for i in z.infolist() if not i.is_dir()]
    items.sort(key=lambda x: x['path'])
    return {'archive_name': path.name, 'sha256': h.hexdigest(), 'file_count': len(items), 'files': items}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--summary-only', action='store_true')
    args = parser.parse_args()
    report = scan(args.zip)
    if args.summary_only: report.pop('files')
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + '\n', encoding='utf-8')
        print(args.output)
    else: print(text)

if __name__ == '__main__': main()
