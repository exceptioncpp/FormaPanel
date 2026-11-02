# Native RH-01 preview from the device YAML

[`host-rh01.yaml`](host-rh01.yaml) compiles the existing
[`rh01-ui.yaml`](../packages/rh01-ui.yaml), Nunito TTFs and RGB565/alpha images
through **ESPHome 2026.10.1 and real LVGL**. It replaces only the physical
display/input/network platform. No separate C UI or browser approximation is
involved; the validated ESP32 entry and UI package remain unchanged.

The backend is the official `snapshot` display: it needs neither SDL2 nor a
graphical desktop. The output is two lossless `480×480` BMP files, lamp on/off.
The capture waits for LVGL's first flush and another 250 ms so the complete
static frame has been drawn. After capture, the process logs
`RH01_NATIVE_PREVIEW_COMPLETE` and stays running; stop it after that marker.

## Run on a Linux build server

Use an existing ESPHome 2026.10.1 environment with GCC/G++, Ninja and the
repository/assets available. The Home Assistant Device Builder container has
to provide those host tools; this does not install anything on Windows.

From the repository root, in that environment:

```sh
# A new output directory is required: snapshot.take refuses to overwrite files.
preview_out="$(mktemp -d /tmp/formapanel-preview.XXXXXX)"
env -u ESPHOME_IS_HA_ADDON ESPHOME_SNAPSHOT_DIR="$preview_out" \
  esphome config firmware/esphome/previews/host-rh01.yaml
env -u ESPHOME_IS_HA_ADDON ESPHOME_SNAPSHOT_DIR="$preview_out" \
  esphome run firmware/esphome/previews/host-rh01.yaml
# Wait for RH01_NATIVE_PREVIEW_COMPLETE, then stop the process (Ctrl+C).
# $preview_out/rh01-on.bmp and $preview_out/rh01-off.bmp are the captures.
```

`ESPHOME_IS_HA_ADDON` is unset for the host invocation so the HA app does not
redirect the native build into its device build location. The explicit
`preview_build_path` substitution defaults to
`build/formapanel-host-rh01`, resolved below ESPHome's data directory
(`.esphome/` beside the entry configuration in a standalone invocation).
It may be overridden to a dedicated writable absolute directory by a wrapper.

When deploying below `/config/esphome/formapanel-rh01/`, use a separate wrapper:

```yaml
substitutions:
  formapanel_asset_dir: formapanel-rh01/assets
  preview_build_path: /data/build/formapanel-host-rh01
packages:
  preview: !include formapanel-rh01/firmware/esphome/previews/host-rh01.yaml
```

Give that wrapper a different filename from the physical device entry. It has
no Wi-Fi, API, OTA or secrets. Its fixed demo substitutions duplicate those
in the physical entry; retain the same values when comparing screenshots.
There is only one UI widget tree and one set of images/fonts.

Convert BMP to PNG with the build environment's existing Pillow when embedding
in a browser or HA picture card. A server may publish the resulting PNG files
and build log in its existing preview page; there is no native HA visual editor
or web streaming server in this profile. Do not treat host rendering as proof
of LCD timing, physical colors, PSRAM performance or touch calibration.

## Optional interactive SDL variant

For mouse interaction on a Linux/macOS desktop, replace the display platform
with `sdl`, add `touchscreen: [{platform: sdl, id: panel_touch,
display: panel_display, sdl_id: panel_display}]`, and retain the shared
`lvgl.touchscreens` instead of removing it. SDL2 development libraries and a
desktop are required. With `headless: true`, SDL receives no mouse/keyboard
events and cannot use the SDL touchscreen; for view-only output this snapshot
profile is simpler. Windows uses WSL if native host execution is desired.

Official sources:

- [Host build and HA connectivity](https://esphome.io/components/host/).
- [Snapshot display and snapshot.take](https://esphome.io/components/display/snapshot/).
- [SDL display, headless mode and dependencies](https://esphome.io/components/display/sdl/).
- [Upstream LVGL host test](https://github.com/esphome/esphome/blob/2026.10.1/tests/components/lvgl/test.host.yaml).
- [Upstream snapshot test](https://github.com/esphome/esphome/blob/2026.10.1/tests/components/snapshot/common.yaml).

Verified on 2026-10-31 in the existing Home Assistant ESPHome 2026.10.1 app:
configuration validation, native compilation, execution and both `480×480`
on/off captures passed. The existing GCC/G++ and Ninja were sufficient; no
SDL2 package or Windows build tools were installed. Both captures were also
converted losslessly to PNG for browser viewing and visually inspected.
