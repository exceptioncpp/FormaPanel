"""Focused checks for the device asset contract and reproducible export."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("render_rh01", ROOT / "tools/render_rh01.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class RH01AssetsTests(unittest.TestCase):
    def test_export_contract_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            exports = renderer.render_all(Path(tmp))
            self.assertEqual(len(exports), 5)
            for path in exports:
                name = path.stem.removeprefix("rh01-")
                with Image.open(path) as actual, Image.open(renderer.OUTPUT / path.name) as committed:
                    self.assertEqual(actual.size, renderer.SIZES[name])
                    self.assertEqual(actual.mode, "RGB" if name == "background" else "RGBA")
                    self.assertEqual(actual.tobytes(), committed.tobytes())

    def test_decorations_have_real_transparency(self):
        for name in ("weather", "wind", "lamp-on", "lamp-off"):
            with self.subTest(name=name), Image.open(renderer.OUTPUT / f"rh01-{name}.png") as im:
                alpha = im.getchannel("A")
                self.assertEqual(alpha.getextrema()[0], 0)
                self.assertGreater(alpha.getextrema()[1], 100)
                self.assertEqual(alpha.getpixel((0,0)), 0)
                self.assertEqual(alpha.getpixel((im.width-1,0)), 0)

    def test_lamp_wire_fades_and_state_geometry_is_shared(self):
        mask = renderer.lamp_mask()
        # Fully absent at top; its opacity rises toward the pendant.
        wire = [mask.getpixel((48*renderer.SCALE,y*renderer.SCALE)) for y in (10,20,28,38,47)]
        self.assertEqual(wire[0],0)
        self.assertEqual(wire[1],0)
        self.assertEqual(wire,sorted(wire))
        self.assertGreater(wire[-1],150)
        on,off = renderer.lamp(True),renderer.lamp(False)
        self.assertEqual(on.size,off.size)
        # The same rim and dome extrema survive both palettes.
        for point in ((31,67),(48,52),(65,67)):
            self.assertGreater(on.getpixel(point)[3],60)
            self.assertGreater(off.getpixel(point)[3],30)
        # Active light extends below the shade; inactive has no halo there.
        self.assertGreater(on.getpixel((48,80))[3],10)
        self.assertEqual(off.getpixel((48,80))[3],0)

    def test_background_does_not_read_composition_reference(self):
        # The only raster input is a clean photographic master.
        self.assertEqual(renderer.SOURCE.name,"golden-sunrise-over-alpine-lake.png")
        self.assertEqual(renderer.background().mode,"RGB")
        self.assertIn("source/backgrounds",renderer.SOURCE.as_posix())


if __name__ == "__main__":
    unittest.main()
