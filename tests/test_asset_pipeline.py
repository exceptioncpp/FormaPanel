import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
SPEC=importlib.util.spec_from_file_location('render_assets',ROOT/'tools/render_assets.py')
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class AssetPipelineTests(unittest.TestCase):
    def test_design_tokens(self):
        data=json.loads((ROOT/'ui/tokens/tokens.json').read_text(encoding='utf-8'))
        self.assertEqual(data['profiles']['s3-480']['width'],480)
        self.assertEqual(data['profiles']['p4-720']['width'],720)
    def test_source_is_svg(self):
        for p in mod.SOURCES.values():
            self.assertTrue(p.exists())
            self.assertIn('<svg',(p.read_text('utf-8')))
    def test_render_both_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            for w in [480,720]:
                output=Path(tmp)/f'{w}.png'
                mod.render(mod.SOURCES['aurora-background'],output,w,w)
                with Image.open(output) as im:
                    self.assertEqual(im.size,(w,w))
                    self.assertEqual(im.mode,'RGB')

if __name__=='__main__': unittest.main()
