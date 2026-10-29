#!/usr/bin/env python3
"""Basic repository/documentation and generated asset consistency check."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
REQUIRED=['README.md','MISSION.md','docs/README.md','docs/01-requirements/requirements.md',
          'docs/02-research/guition-factory-demo.md','docs/03-design/resolution-strategy.md',
          'docs/05-roadmap/roadmap.md','ui/tokens/tokens.json']

def validate():
    errors=[]
    for path in REQUIRED:
        if not (ROOT/path).is_file(): errors.append(f'Missing {path}')
    tokens=json.loads((ROOT/'ui/tokens/tokens.json').read_text('utf-8'))
    for name, profile in tokens['profiles'].items():
        res=f"{profile['width']}x{profile['height']}"
        for asset in ('aurora-background','room-home-preview'):
            path=ROOT/f'assets/generated/{res}/{asset}.png'
            if not path.exists():
                errors.append(f'Missing generated {path}')
            else:
                with Image.open(path) as im:
                    if im.size!=(profile['width'],profile['height']): errors.append(f'Wrong dimensions: {path}')
    return errors

if __name__=='__main__':
    errors=validate()
    if errors:
        print('\n'.join(errors)); raise SystemExit(1)
    print('PASS: required docs and generated assets are consistent')
