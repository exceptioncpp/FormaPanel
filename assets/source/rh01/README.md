# RH-01 device assets

Rebuild with `python tools/render_rh01.py` after installing `tools/requirements.txt`.
The generator needs only Pillow. Output is tracked in `assets/generated/480x480/`.
`manifest.json` records the source and export checksums, placements, and validation.

The photograph remains a clean, separate master in `assets/source/backgrounds/`.
Its output has a smooth readability grade, with no flattened clock or sensor text.
Weather, wind and lamp are antialiased procedural decorations. Both lamp states
use the same `lamp_mask()` and canvas. No image-generation service or copied
third-party icon set is used for these decorations.

All positions refer to the top-left of each image on the 480×480 display:

| File | Format | Dimensions | Position |
| --- | --- | --- | --- |
| rh01-background.png | RGB | 480×480 | 0, 0 |
| rh01-weather.png | RGBA | 64×54 | 30, 27 |
| rh01-wind.png | RGBA | 28×26 | 160, 43 |
| rh01-lamp-on.png | RGBA | 96×112 | 374, 336 |
| rh01-lamp-off.png | RGBA | 96×112 | 374, 336 |

The visible lamp dome spans approximately x=405…439, y=388…405 globally.
The invisible touch area is defined separately by the firmware. The wire fades
to full transparency near global y=356, rather than extending to the screen edge.
These assets are visually reviewed, but their alpha blending and glow still
require verification on the physical display.
