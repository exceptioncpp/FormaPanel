# Реестр источников исследования прошивки и LVGL tooling

**Дата контрольного среза:** 2026-10-29. Это companion к [firmware platforms](firmware-platforms-2026-10.md), [visual tools](lvgl-visual-tools-2026-10.md), [build/preview](build-preview-workflows.md) и [RH-01 A/B](../06-validation/rh01-platform-ab-test.md).

## Принципы проверки

- **A** — официальный upstream документ, release, SPDX/license. Это не подтверждение успешной работы FormaPanel.
- **B** — community исходники с README или CI; конкретная ревизия нашей панели ещё не испытана.
- **C** — визуальный/продуктовый reference или маркетинговая демонстрация без воспроизводимого устройства.
- **V** — собственное измерение FormaPanel с фото/log/commit. **На 29.10.2026 таких данных нет.**

Различать поддержку всего ESP32-S3 и поддержку конкретной Guition RGB панели; совместимость LVGL 9 API и корректность кадра на RGB565; работу web editor и тот же compiled LVGL renderer; опубликованную версию и план release.

## 1. Firmware, hardware, SDK

| Код | Source | Доказуемое свойство / ограничение |
|---|---|---|
| F-01 | [ESPHome LVGL](https://esphome.io/components/lvgl/) | Официальный YAML слой над LVGL, 9.x; A. Не весь native C API доступен YAML. |
| F-02 | [ESPHome mipi_rgb](https://esphome.io/components/display/mipi_rgb/) | Модель `GUITION-4848S040`; A. Pin-compatible ревизию проверить отдельно. |
| F-03 | [ESPHome Devices Guition](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/) | ESP32-S3, ST7701S/GT911, PSRAM в sample profile; A/B. |
| F-04 | [ESPHome native API](https://esphome.io/components/api/) | Home Assistant integration, actions, encrypted API; A. |
| F-05 | [ESPHome fonts](https://esphome.io/components/font/) | Local TTF / glyph conversion; A, Cyrillic bitmap измерить. |
| F-06 | [ESPHome image](https://esphome.io/components/image/) | Изображения/конвертер; A, alpha + RGB565 проверить. |
| F-07 | [ESPHome releases](https://github.com/esphome/esphome/releases) | 2026.10.0 опубликован 21.10.2026; A. **2026.10.1 в релизах на дату исследования не подтверждён.** |
| F-08 | [ESP-IDF releases](https://github.com/espressif/esp-idf/releases) | v6.1 опубликован 27.08.2026; A. |
| F-09 | [ESP-IDF Windows setup](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/index.html) | EIM, SDK toolchain; A. |
| F-10 | [Espressif esp_lvgl_port](https://components.espressif.com/components/espressif/esp_lvgl_port) | Integration ESP-IDF and LVGL; A. Exact compatibility pin TBD. |
| F-11 | [LVGL](https://github.com/lvgl/lvgl) и [MIT license](https://lvgl.io/docs/open/introduction/license) | Полный LVGL C runtime и license; A. |
| F-12 | [PlatformIO Espressif32](https://docs.platformio.org/en/latest/platforms/espressif32.html) | Build/framework tooling; A, не самостоятельная прошивка. |
| F-13 | [Zephyr ESP32-P4 board](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/espressif/esp32p4_function_ev_board) | Upstream family board; A, не будущая FormaPanel плата. |
| F-14 | [NuttX ESP32-P4](https://nuttx.apache.org/docs/latest/platforms/risc-v/esp32p4/index.html) | P4 support matrix; A, graphics support меняется. |
| F-15 | [Mongoose OS](https://mongoose-os.com/docs/README.md) | IoT SDK; A, Guition first-class support не подтверждена. |

Исторические issues аппаратного профиля: [ESPHome #17784 rotation](https://github.com/esphome/esphome/issues/17784), [ESPHome #17810 timing](https://github.com/esphome/esphome/issues/17810). **Не считать их актуальными ошибками 2026.10.0 без повторной проверки** state/affected versions/fix.

## 2. Базы и UI-референсы сообщества

| Source | Роль, класс, граница применения |
|---|---|
| [openHASP](https://www.openhasp.com/) | B, отдельный MQTT+JSONL LVGL runtime; не ESPHome YAML. |
| [Tessera](https://github.com/MaxGramser/homeassistant_espscreen) | B, editor/manager/multiple panels; не automatic full-custom UI foundation. |
| [EspControl](https://jtenniswood.github.io/espcontrol/screens/4848s040) | B/C, готовые интерфейсы/навигация; дизайн более карточный. |
| [PrayerfulDrop Guition](https://github.com/PrayerfulDrop/ESPHome-Guition-ESP32-S3-4848S040) | B, ESPHome themes/examples; проверить версию/лицензию. |
| [alaltitov Guition](https://github.com/alaltitov/Guition-ESP32-S3-4848S040) | B, UI и RU примеры; проверить актуальность. |
| [VahaC Guition](https://github.com/VahaC/ESP32-4848S040-EspHome-LVGL) | B, HA dashboard example; проверить pinout. |
| [jtenniswood esphome-lvgl](https://github.com/jtenniswood/esphome-lvgl/tree/main/guition-esp32-s3-4848s040) | B, packages/assets example; не готовый проект FormaPanel. |
| [LVGL modular buttons](https://github.com/agillis/esphome-modular-lvgl-buttons) | B, reusable widgets; compatibility TBD. |
| [ESPHome UI Kit](https://github.com/mplogas/esphome-ui-kit) | B, темы/компоненты; license/maintenance TBD. |

Заводская Guition firmware/demo — ранний разбор [factory demo](guition-factory-demo.md), там LVGL 8.3.9. Не копировать проприетарную графику и исходники без проверки прав.

## 3. Редакторы и симуляторы

| Код | Source | Достоверность / проблема |
|---|---|---|
| U-01 | [ESPBoards Designer](https://lvgl.espboards.dev/) | Hosted editor; C/vender. |
| U-02 | [ESPBoards guide](https://lvgl.espboards.dev/help/guide/add-lvgl-design/) | A (vendor docs): ESPHome YAML import/export. Нет доказанного CLI. |
| U-03 | [ESPBoards terms](https://lvgl.espboards.dev/terms/) | A (vendor terms): проверить ограничения hosted/copyright. |
| U-04 | [ESPHomeDesigner](https://github.com/koosoli/ESPHomeDesigner) | B: GPL-3, HA-aware, display lambda/LVGL YAML; **LVGL Highly Experimental**. |
| U-05 | [ESPHome-LVGL-Simulator](https://github.com/MaxCRRR/ESPHome-LVGL-Simulator) | B: MIT, browser JS YAML renderer, не real LVGL; lambdas placeholders. |
| U-06 | [EEZ Studio](https://github.com/eez-open/studio) + [FAQ](https://github.com/eez-open/studio/wiki/FAQ) | A/B: open-source, native C LVGL vs Flow runtime — разные схемы. |
| U-07 | [SquareLine Studio](https://squareline.io/) + [changelog](https://docs.squareline.io/docs/miscellanos/changelog/) | Vendor docs: 1.6.2, 10.08.2026, LVGL 9.5; license/target pin TBD. |
| U-08 | [SquareLine export](https://docs.vision.squareline.io/docs/export/) | Vendor docs: generated C UI, **не** ESPHome YAML. |
| U-09 | [LVGL PC SDL](https://github.com/lvgl/lv_port_pc_vscode) | A: исполняет реальный LVGL на Windows/Linux; нужно собственное UI core/mocks. |
| U-10 | [LVGL Pro Editor](https://lvgl.io/docs/pro/editor/overview) | A: XML, visual editor, native LVGL preview, custom C widgets. |
| U-11 | [LVGL Pro CLI](https://lvgl.io/docs/pro/cli) | A: generate/test/screenshots, **требует коммерческой лицензии**. |
| U-12 | [LVGL Pro license](https://lvgl.io/docs/pro/editor/license) и [pricing](https://lvgl.io/pro/pricing) | A: Community Editor для personal/noncommercial, Product tier ~$20k/product на дату среза; цену обновлять перед решением. |

**Отдельные классы:** Figma/Inkscape/Python рендер — static reference, не LVGL; WebAssembly preview может выполнять настоящую LVGL библиотеку только с конкретно собранным и pinned `ui_core`, **не** arbitrary ESPHome YAML. Generic VS Code editor — не гарантия fidelity и не GUI exporter.

## 4. Открытые проверки / future evidence

1. Фото PCB, точная модель/маркировка, boot logs, partitions, фактические PSRAM и Flash.
2. ESPHome 2026.10.0 display+touch smoke, OTA/backlight, повороты/тестовая сетка.
3. Альфа, wire fade, blend, dithering и sprite memory для [LA-01](../03-design/light-action-reference-LA-01.md).
4. Nunito/Comfortaa кириллица, размер glyph cache, RGB565 pixel-level screenshot vs LCD photo.
5. ESPBoards round-trip реального `lvgl:` YAML, сохранность lambdas/packages.
6. ESPHomeDesigner LVGL YAML export compatibility и Windows runtime.
7. ESPHome-LVGL-Simulator local images/fonts/HA mocks, пределы renderer parity.
8. LVGL Pro/EEZ/SquareLine — C export в **один** pinned LVGL 9 build для SDL и IDF.
9. p50/p95/p99 redraw/touch, heap, PSRAM, flash, HA reconnection.
10. Выбор ESP32-P4 720 платы, network coprocessor/display/touch; P4 compatibility пока прогноз, не факт.
11. SPDX, vendor/font/art provenance; [legal policy](../07-legal/licensing.md).

**Протокол пополнения:** для каждого ответа — source commit/tag, дата, версия/ревизия, минимальный репродуктор, фото/log, статус issue. Никаких меток «on-device verified» до реальных запусков.

## 5. Происхождение

Эта серия Markdown — структурированный перенос выводов Deep Research от 29.10.2026 с повторной сверкой официальных release pages. Это **не** дословный транскрипт и **не** доказательство аппаратных испытаний. Внешние сайты могут измениться; для релиза фиксировать git SHAs, версии и лицензии. Расширенный исходный отчёт хранится в отдельной сессии Deep Research, его Markdown-файл в текущий репозиторий не импортировался.
