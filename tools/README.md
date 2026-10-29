# Developer tools

- `render_assets.py`: render original SVGs at 480 and 720 (CairoSVG + Pillow antialiasing).
- `vendor_inventory.py`: safe vendor ZIP inventory (path, size, hash of archive). It never extracts or publishes bundled code/images.
- `validate.py`: check source layout, token syntax, target profiles, rendered PNG output.

```bash
pip install -r tools/requirements.txt
python tools/render_assets.py --all
python tools/validate.py
python -m unittest discover -s tests -v
```
