# Firmware

Target: ESPHome with native LVGL for Guition S3 480; experimental native ESP-IDF path kept separate.

The first RH-01 visual firmware is implemented in [esphome](esphome/README.md),
with local fonts, RGB565 background, alpha icons and an interactive demo lamp.
Read the [build report](../docs/06-validation/rh01-build-2026-10-29.md) for actual
validation status. Values are mock data; physical Guition acceptance is pending.
The native ESP-IDF candidate remains unimplemented.

Start with the [development map](../docs/development.md),
[source composition rules](../docs/04-architecture/source-composition.md) and
[build/preview runbook](../docs/06-validation/build-and-preview-runbook.md).
