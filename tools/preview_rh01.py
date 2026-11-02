#!/usr/bin/env python3
"""Local RH-01 preview using the documented ESPHome-LVGL-Simulator.

Only substitutions, font, image and lvgl are exported; no network/secrets.
The pinned browser renderer gets a small, explicit adapter for actual PNGs,
font metrics and this demo's lamp. This is not a native LVGL framebuffer.
"""
import argparse
import functools
import hashlib
import http.server
import json
import math
from pathlib import Path
import shutil
import urllib.request

from PIL import ImageFont
import yaml

ROOT = Path(__file__).resolve().parent.parent
REVISION = "170517631c1f77b107fcac254a3a5d758b826c48"
UPSTREAM_SHA256 = "5d175a6fb986ac43228ffd89a6b978a50799964b977e8f69c9a5ec193019ea09"
DEST = ROOT / "reports/local/rh01-preview"


def prepare():
    DEST.mkdir(parents=True, exist_ok=True)
    cached = ROOT / "reports/local/ESPHome-LVGL-Simulator/index.html"
    if not cached.exists():
        cached.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(
            f"https://raw.githubusercontent.com/MaxCRRR/ESPHome-LVGL-Simulator/{REVISION}/index.html", cached)
    source = cached.read_text("utf-8")
    if hashlib.sha256(cached.read_bytes()).hexdigest() != UPSTREAM_SHA256:
        raise RuntimeError("Simulator file differs from the pinned upstream revision")
    # Includes and secrets are deliberately not interpreted by this export.
    class Loader(yaml.SafeLoader):
        pass
    Loader.add_multi_constructor("!", lambda loader, tag, node: loader.construct_scalar(node))
    entry = yaml.load((ROOT / "firmware/esphome/formapanel-rh01.yaml").read_text("utf-8"), Loader)
    ui = yaml.safe_load((ROOT / "firmware/esphome/packages/rh01-ui.yaml").read_text("utf-8"))
    export = {"substitutions": {k: v for k, v in entry["substitutions"].items() if k.startswith("demo_")},
              "display": [{"dimensions": {"width": 480, "height": 480}}], **ui}
    images, metrics = {}, {}
    for item in export["image"]:
        for key, value in entry["substitutions"].items():
            item["file"] = item["file"].replace("${" + key + "}", str(value))
        path = (ROOT / "firmware/esphome" / item["file"]).resolve()
        shutil.copy2(path, DEST / path.name)
        item["file"] = path.name
        images[item["id"]] = path.name
    for item in export["font"]:
        for key, value in entry["substitutions"].items():
            item["file"] = item["file"].replace("${" + key + "}", str(value))
        path = (ROOT / "firmware/esphome" / item["file"]).resolve()
        (DEST / "fonts").mkdir(exist_ok=True)
        shutil.copy2(path, DEST / "fonts" / path.name)
        item["file"] = "fonts/" + path.name
        font = ImageFont.truetype(str(path), item["size"])
        metrics[item["id"]] = {"size": item["size"], "ascent": font.getmetrics()[0],
                              "advance": {c: math.ceil(font.getlength(c)) for c in item["glyphs"]}}
    class Dumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)
    def hex_colors(tree):
        if isinstance(tree, dict):
            for key, value in tree.items():
                if key.endswith("color") and isinstance(value, int):
                    tree[key] = f"0x{value:06X}"
                else:
                    hex_colors(value)
        elif isinstance(tree, list):
            for item in tree:
                hex_colors(item)
    hex_colors(export)
    text = yaml.dump(export, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=120)
    (DEST / "rh01-preview.yaml").write_text(text, "utf-8")
    adapter = r'''
<style>#bezel{display:none}#frame{border:0;padding:0;box-shadow:none}#cv{image-rendering:auto}</style>
<script>
// FormaPanel adapter: upstream uses placeholders for images and font size*.82.
// Use the real PNGs, nominal font size and FreeType ascent used by ESPHome.
const fpFiles = __IMAGES__, fpMetrics = __METRICS__, fpImages = {};
const fpOriginalDraw = drawWidget;
drawWidget = function(w, px=0, py=0, depth=0) {
  if(w.hidden) return;
  const x=px+w.ax,y=py+w.ay;
  if(w.type==='image') {
    w._absX=x; w._absY=y;
    let src=w.src;
    if(w.widgetId==='rh01_lamp_image') src=fpLampOn?'rh01_lamp_on':'rh01_lamp_off';
    const image=fpImages[src];
    if(image) ctx.drawImage(image,x,y,w.ww,w.wh);
    return;
  }
  if(w.type==='label') {
    const name=w.fontName||'rh01_font_climate', m=fpMetrics[name];
    ctx.save();ctx.font=fcss(name,m.size);ctx.fillStyle=w.color==='#fff'?'#fffef5':w.color;
    ctx.textBaseline='alphabetic';ctx.textAlign='left';
    let cursor=x;
    for(const ch of w.text) {ctx.fillText(ch,cursor,y+m.ascent);cursor+=m.advance[ch]||ctx.measureText(ch).width;}
    ctx.restore();return;
  }
  // Upstream forcibly re-centers button children, even with explicit x/y.
  if(w.widgetId==='rh01_lamp_button') {
    w._absX=x;w._absY=y;
    w.children.forEach(c=>drawWidget(c,x,y,depth+1));return;
  }
  fpOriginalDraw(w,px,py,depth);
};
let fpLampOn=true;
cv.addEventListener('click', e=>{
  const r=cv.getBoundingClientRect(),x=(e.clientX-r.left)*480/r.width,y=(e.clientY-r.top)*480/r.height;
  if(x>=366&&x<478&&y>=332&&y<460) {fpLampOn=!fpLampOn;redraw();}
});
const fpSave=document.createElement('button');fpSave.textContent='Сохранить PNG';
fpSave.onclick=async()=>{await fetch('/capture',{method:'POST',body:cv.toDataURL('image/png').split(',')[1]});fpSave.textContent='PNG сохранён';};
document.getElementById('edh').appendChild(fpSave);
const fpNote=document.createElement('div');fpNote.style='padding:8px;color:#c5ac7e';
fpNote.textContent='FormaPanel · RH-01 · browser approximation + local PNG/font adapter · demo values · no HA commands';
document.getElementById('mid').prepend(fpNote);
// Disable the optional external AI analyzer and unrelated CDN icon loading.
analyzeConfig=()=>{};
Promise.all(Object.entries(fpFiles).map(async([id,path])=>{
  const im=new Image();im.src=path;await im.decode();fpImages[id]=im;
})).then(async()=>{
  document.getElementById('yaml').value=__YAML__;
  updateLN();run();
  await document.fonts.ready;
  Object.entries(fpMetrics).forEach(([id,m])=>FMAP[id]=m.size);
  run();redraw();
});
</script>
'''.replace("__IMAGES__", json.dumps(images)).replace("__METRICS__", json.dumps(metrics)).replace("__YAML__", json.dumps(text, ensure_ascii=True))
    # Drop automatic remote icon font downloads (RH-01 has only local PNGs).
    source = source.replace("tryLoadFont('MDI',['./fonts/materialdesignicons-webfont.woff2','./fonts/materialdesignicons-webfont.ttf','https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/fonts/materialdesignicons-webfont.woff2']);", "")
    # Upstream records IDs only for containers; the lamp image also needs one.
    source = source.replace("src:gp('src')||'',", "src:gp('src')||'',widgetId:gp('id')||'',")
    (DEST / "index.html").write_text(source.replace("</body>", adapter + "</body>"), "utf-8")
    (DEST / "provenance.json").write_text(json.dumps({"simulator_commit": REVISION, "upstream_html_sha256": hashlib.sha256(cached.read_bytes()).hexdigest(), "adapter": "tools/preview_rh01.py", "native_lvgl": False}, indent=2), "utf-8")
    return DEST


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        import base64
        if self.path != "/capture":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            self.send_error(413)
            return
        (DEST / "rh01-preview.png").write_bytes(base64.b64decode(self.rfile.read(length), validate=True))
        self.send_response(200)
        self.end_headers()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    folder = prepare()
    print(f"Preview: http://127.0.0.1:{args.port}/ — {folder}", flush=True)
    if not args.prepare_only:
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(folder))).serve_forever()
