# ESPHome firmware (planned)

Proposed structure after hardware bring-up:

```text
firmware/esphome/
  boards/guition-s3-480.yaml
  packages/system/{wifi,api,ota,backlight,display,touch}.yaml
  packages/ui/{theme,fonts,widgets,pages}.yaml
  panels/{living,bedroom,office,bathroom,hallway}.yaml
  secrets.yaml.example
```

Use `packages` and `substitutions` for different rooms; avoid duplicating UI screen declarations. **No functional YAML is supplied yet** because hardware pins, flash/PSRAM and ESPHome version require confirmation.
