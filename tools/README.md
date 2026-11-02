# Developer tools

- `render_assets.py`: render original SVGs at 480 and 720 (CairoSVG + Pillow antialiasing).
- `vendor_inventory.py`: safe vendor ZIP inventory (path, size, hash of archive). It never extracts or publishes bundled code/images.
- `validate.py`: check source layout, token syntax, target profiles, rendered PNG output.
- `render_rh01.py`: reproducible photo grading and transparent RH-01 weather/wind/lamp assets, without baked text.
- `preview_rh01.py`: local preview of the firmware's UI tree using a pinned ESPHome-LVGL-Simulator and actual PNG/TTF resources. [Details and limitations](../docs/03-design/rh01-implementation.md).
- `ha-workbench/`: installed HA app source (0.1.1), shared checkout builds and real host/snapshot LVGL frames. [Build/preview runbook](../docs/06-validation/build-and-preview-runbook.md).

```bash
pip install -r tools/requirements.txt
python tools/render_assets.py --all
python tools/render_rh01.py
python tools/validate.py
python -m unittest discover -s tests -v
```

Preview: `python tools/preview_rh01.py`, then open `http://127.0.0.1:8080/`.
Firmware compilation happens on Home Assistant, with no local ESP32 SDK.
