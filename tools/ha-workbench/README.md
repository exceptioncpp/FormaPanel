# FormaPanel Workshop for Home Assistant

This local HA app reads the **same Git checkout** that Studio Code Server edits.
ESPHome processes the real entry YAML, all `packages`/`!include`, fonts, images
and profile substitutions. There is no editor-to-builder import/export step.

The app offers three operations for profiles in `config/workbench-targets.json`:

- Validate the device configuration.
- Compile Factory/OTA binaries without installing them on a device.
- Compile and run the shared UI using ESPHome's host/snapshot backend, then show
  actual LVGL PNG frames, including lamp states and shared secondary pages.

The read-only source mount is `/homeassistant/esphome/formapanel-rh01` by default.
Build caches and output go to the app's private `/data` volume. One job runs at
a time. The source hash next to each preview detects changes made after capture.
From 0.1.1 the wrapper `/data/configs/<kind>-<profile>.yaml` and ESPHome metadata
`/data/esphome/<kind>/<profile>` keep a stable identity between jobs, allowing
incremental compilation. Capture files and logs remain unique per job. The first
build after this migration fills the metadata once. Saving YAML does not yet
start a build automatically; use the preview button.
Git remains available in Studio Code Server; the workbench shows branch, commit
and uncommitted state but does not commit, pull or push automatically.

## Install as a local HA app

Copy this folder to the HA local apps directory, reload the app store, install
FormaPanel Workshop and start it. The container derives from the pinned official
ESPHome 2026.10.1 build image. Enable Show in sidebar. No HA restart is needed.
Detailed commands and actual installation status belong in the environment's
validation report.

The app uses HA Ingress and opens no host port. It has no Supervisor, Home
Assistant API, Docker socket or hardware access. Its HTTP server accepts only
Supervisor ingress and container-local health probes. Sources are read-only;
private `secrets.yaml` files stay ignored by Git. BIN files contain provisioned
device credentials and are served only through authenticated Ingress.

Source configuration can execute C++ during a native build. This is a developer
tool for a trusted repository and HA administrators, not a public upload service.
There are no file upload or arbitrary command endpoints.

## Local development

Only the server's Python/Pillow/PyYAML dependencies are required to check its
HTTP contract. Set `FORMAPANEL_WORKSPACE` to a checkout and `FORMAPANEL_DATA` to
a disposable output directory before running `python server.py`. ESPHome and
GCC are needed only where compilation actually takes place (HA in this setup).

The web app must use relative URLs so it works below HA's per-install ingress
prefix. Available routes: `GET api/state?profile=...`, `POST api/jobs`, and
generated `files/<job>/<artifact>` links. A rejected concurrent build returns
HTTP 409. The server never calls `esphome run` for physical devices or `upload`.
