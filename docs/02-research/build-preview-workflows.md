# FormaPanel — build, preview и CI (Windows 11 / GitHub Actions)

**Статус:** исследование и проектируемый workflow, 29.10.2026. Команды ниже **не запускались**, а реальные firmware проекты ещё не созданы. Сейчас `.github/workflows/verify.yml` проверяет графику/Python, **не** ESPHome/ESP-IDF. См.: [сравнение платформ](firmware-platforms-2026-10.md), [визуальные редакторы](lvgl-visual-tools-2026-10.md), [проверка RH-01](../06-validation/rh01-platform-ab-test.md).

## 1. Как не дублировать UI

```text
RH-01, LA-01 approved design + assets/source/*
                   │
          tools/render_assets.py
                   │
        assets/generated/{480x480,720x720}
                   │
       ┌───────────┴─────────────┐
       ▼                         ▼
ESPHome LVGL YAML            Native LVGL C / generated C
       │                         │
ESPBoards/JS preview         LVGL SDL PC preview
       │                         │
ESPHome S3 binary            ESP-IDF S3 binary
       └────────────┬────────────┘
                    ▼
             Guition hardware A/B
```

**Общее**: утверждённая сетка, background files, LA-01 sprite states, glyph set, mock sensor values, тестовые сценарии. **Раздельное**: YAML widgets у ESPHome и C/C++ objects у native — это именно два *коротких сравнительных* эксперимента, а не два поддерживаемых production UI.

- **ESPHome single source of truth:** отслеживаемый Git `lvgl:` YAML; ESPBoards только экспорт/импорт, браузерный simulator только предварительный render. Пользовательские `!lambda`, ESPHome `packages` и external C++ могут быть не представлены в GUI.
- **Native single source of truth:** независимо от GUI editor — C UI core / редактируемый XML или EEZ project + generated source в Git. Один `ui_core` компилируется **и** в host SDL, **и** в ESP-IDF. Весь ESP32-specific код вынести в `board_guition`; сети/HA — в `ha_bridge`; данные на PC — в `mock_state`.
- **Запрещённая предпосылка:** готовый C-код SquareLine/EEZ/LVGL Pro не становится ESPHome YAML автоматически. Нет универсального совместимого двустороннего конвертера.

## 2. Подготовка Windows 11

Установить Git, Python 3.12, VS Code, CMake/Ninja и, при native ветке, официальный Espressif Installation Manager + SDL2 через vcpkg. Для visual authoring установить или открыть один из редакторов. Убедиться, что используемая исходная ветка FormaPanel соответствует PR/`main`.

```powershell
cd D:\Work\Projects\Home\panels\FormaPanel
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r tools/requirements.txt
python tools/render_assets.py --all
python tools/validate.py
python -m unittest discover -s tests -v
```

Первые команды работают с существующим asset pipeline. Текущие зависимости Python заданы диапазонами: после выбора baseline создать lockfile с версиями/хешами и использовать его в локальной среде и Actions.

## 3. ESPHome lane — подготовка и build

Предложение структуры:

```text
firmware/esphome/
  boards/guition-s3-480.yaml
  packages/system/{display,touch,backlight,network,api,ota}.yaml
  packages/ui/{fonts,assets,theme,rh01}.yaml
  panels/{living,bedroom,office,bathroom,hallway}.yaml
  secrets.yaml.example
```

Эти YAML **пока не существуют**. У дисплея есть [официальный ESPHome preset](https://esphome.io/components/display/mipi_rgb/) `GUITION-4848S040`, но прежде всего проверить маркировку/ревизию платы, backlight, PSRAM, I²C GT911 и RGB timings. Не копировать guessed pins в firmware.

На дату исследования **ESPHome 2026.10.0** опубликован в [releases](https://github.com/esphome/esphome/releases). Упоминание `2026.10.1` в исходном Deep Research черновике было неподтверждённым — здесь исправлено.

```powershell
python -m pip install "esphome==2026.10.0"
# Эти три команды — только ПОСЛЕ добавления living-rh01.yaml:
python -m esphome config firmware/esphome/panels/living-rh01.yaml
python -m esphome compile firmware/esphome/panels/living-rh01.yaml
python -m esphome analyze-memory firmware/esphome/panels/living-rh01.yaml
```

Первую прошивку `run --device COMx` выполнять **только после** осмотра платы, сохранения заводского firmware/flash dump при возможности и serial smoke-test. Для mock CI не применять настоящие Wi-Fi/API/OTA secrets. Подменять `!secret` тестовыми значениями; не загружать их в публичные browser editors.

### Desktop preview из *того же* YAML

1. В [ESPBoards Designer](https://lvgl.espboards.dev/) импортировать отдельный RH-01 LVGL fragment, редактировать позиции, background, widgets, export YAML. Проверить `git diff`: неизвестные директивы могут потеряться.
2. В [ESPHome-LVGL-Simulator](https://github.com/MaxCRRR/ESPHome-LVGL-Simulator) вставить итоговый YAML и быстро проверить геометрию, pages, навигацию и цвета. Это browser interpretation, не native LVGL.
3. Запустить `esphome config` / `esphome compile`. Проверить реальную точность и прозрачность **на Guition**.

Локальный simulator:

```powershell
git clone https://github.com/MaxCRRR/ESPHome-LVGL-Simulator.git
cd ESPHome-LVGL-Simulator
py -3 -m http.server 8080
# http://localhost:8080/index.html
```

Сначала закрепить выбранный Git commit симулятора. Его дополнительный AI analyzer необязателен; внешние API ключи не нужны. HA states и `!lambda` могут заменяться placeholders/random values. Нельзя использовать browser screenshot как pixel-perfect эталон.

### CI sketch после создания firmware

```yaml
name: Firmware experiment
on:
  push:
    branches: [main]
  pull_request:
jobs:
  esphome-rh01:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "esphome==2026.10.0"
      - run: esphome config firmware/esphome/panels/living-rh01.yaml
      - run: esphome compile firmware/esphome/panels/living-rh01.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: esphome-rh01
          path: firmware/esphome/.esphome/**/*.bin
          if-no-files-found: error
```

**Не добавлять job сейчас:** путь generated firmware, наличие конфигов и разрешение dependencies не проверены. После первого green run закрепить версии Actions по SHA и собирать 5 комнат матрицей, когда существуют все room profiles. Опционально собирать elf/map и report памяти (реальное CLI поведение проверять с `esphome --help`).

## 4. Native ESP-IDF lane и реальный LVGL SDL preview

```text
firmware/native/
  CMakeLists.txt
  sdkconfig.defaults
  dependencies.lock
  components/
    board_guition/      # RGB ST7701, GT911, backlight, PSRAM
    ui_core/            # pure LVGL C: RH-01, LA-01, animations, assets
    ha_bridge/          # MQTT or HA bridge: state/commands/ack/OTA
  main/
tools/preview/lvgl-pc/
  CMakeLists.txt
  main.c
  mocks/
```

ESP-IDF `v6.1` опубликован — [releases](https://github.com/espressif/esp-idf/releases), [Windows install](https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/index.html). Для firmware pin managed components `espressif/esp_lvgl_port`, `lvgl/lvgl` и `esp_lcd_touch` в manifest + lockfile **после проверки совместимой комбинации**. Не использовать непроверенные `^latest`.

```powershell
# В установленной ESP-IDF PowerShell environment:
cd D:\Work\Projects\Home\panels\FormaPanel\firmware\native
idf.py set-target esp32s3
idf.py build
idf.py size
```

Для PC:
- Стартовать от официального [LVGL lv_port_pc_vscode](https://github.com/lvgl/lv_port_pc_vscode), pin commit/submodules.
- Использовать CMake + Ninja + Windows MSVC и согласованный vcpkg triplet, например `vcpkg install sdl2:x64-windows`. Версии SDL и параметры CMake уточнить по закреплённому revision.
- Подключить **тот же** `ui_core`, что включён в `firmware/native`; SDL mouse/touch, host clock, mock HA entity events вместо железа и сети.
- Для 480×480/720×720 выбрать правильный `LV_COLOR_DEPTH`, font bitmaps, image decoder, LVGL configuration, чтобы снизить визуальное расхождение.
- Встроить screenshot/test API уже в **наш** executable. Команда `formapanel-preview --test` пока **не реализована**.

Native UI authoring варианты:
- **LVGL Pro Editor**: XML + visual Design mode, live real LVGL, code generation; Community Editor бесплатен для личных проектов, но **CLI** для автоматизированной генерации/тестов лицензируется отдельно ([docs](https://lvgl.io/docs/pro/cli), [license](https://lvgl.io/docs/pro/editor/license)). Не вводить в обязательный free CI.
- **EEZ Studio**: `.eez-project` → C, без обязательного EEZ Flow runtime, если используется native export; хранить handwritten actions вне generated.
- **SquareLine**: desktop visual editor → generated C, нужен license/export policy.

Пример отдельного native firmware job **после появления проекта**:

```yaml
  native-rh01:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: espressif/esp-idf-ci-action@v1
        with:
          esp_idf_version: v6.1
          target: esp32s3
          path: firmware/native
```

Пример Linux SDL host prerequisites: `sudo apt-get install -y build-essential cmake libsdl2-dev xvfb`, затем `cmake --build` и `xvfb-run` с **реализованным в проекте** mock screenshot runner. Ни один screenshot без физической IPS проверки не доказывает качество градиентов, отклика touch и стабильности DMA/PSRAM.

## 5. Контрольные точки, артефакты и CI policy

| Проверка | Сейчас | Рекомендуемый CI status |
|---|---|---|
| SVG/PNG render 480/720, unit tests | Есть `verify.yml` | Blocking |
| Glyph coverage Cyrillic + font/image manifest/rights | Нет | Blocking после внедрения |
| ESPHome YAML schema и S3 compile | Нет | Blocking при наличии PoC |
| Native ESP-IDF S3 compile | Нет | Blocking при наличии PoC |
| Native SDL screenshots and mocks | Нет | Blocking после реального harness |
| ESPHome browser render | Нет | Advisory, **не** визуальный oracle |
| Реальный Guition 480 IPS / GT911 / HA / OTA | Не проверено | Manual acceptance gate, логи/фото |
| P4 720 | Плата не выбрана | Deferred |

**GitHub Actions artifacts:** `firmware.bin`, `.elf`, `.map`, UI screenshots, resource/latency reports (если генераторы написаны). Не публиковать пригодные для случайной установки бинарники без утверждённого hardware profile и recovery plan. Не выкладывать фабричные файлы/сторонние изображения без лицензии.

## 6. Безопасность и поддержка пяти панелей

- Home Assistant — source of truth; кнопка light action проходит `off → pending → confirmed/on` или `unavailable`, не выдавая optimistic action за факт. Реальные действия HA не нужны для mock preview.
- Настоящие secrets — только `secrets.yaml`/локальный provision + GitHub Actions secrets (не в job logs). Native MQTT — TLS/auth, reconnect, expiry, stale data; ESPHome — encrypted API + OTA.
- Разделить общий UI layout для living/bedroom/office и room-specific backgrounds/entity mapping, не копировать пять полных файлов UI.
- Миграция на ESP32-P4 — **новый board/display/network слой** и новый hardware validation; не только resize canvas.
- Первое решение [ADR-0003](../04-architecture/adr/0003-platform-evaluation.md) принять после A/B PoC [RH-01/LA-01](../06-validation/rh01-platform-ab-test.md).
