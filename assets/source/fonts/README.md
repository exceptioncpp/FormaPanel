# Nunito

The bundled Nunito family is distributed under the SIL Open Font License 1.1,
included in `OFL.txt`. `manifest.json` records its upstream location and checksums.

`Nunito-Bold.ttf` and `Nunito-Medium.ttf` are static instances at weights 700 and
500. The original `Nunito-Variable.ttf` is retained to regenerate them with
fontTools 4.68.0:

```python
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

for name, weight in (("Bold", 700), ("Medium", 500)):
    font = TTFont("Nunito-Variable.ttf")
    font = instantiateVariableFont(font, {"wght": weight},
                                   inplace=True, updateFontNames=True)
    font.save(f"Nunito-{name}.ttf")
```

The firmware consumes the static instances; it does not need fontTools or an
online font download.
