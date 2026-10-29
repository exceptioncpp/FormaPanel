# LVGL: визуальные редакторы и предпросмотр без прошивки (29.10.2026)

**Статус:** research / tool evaluation, не принятый инструмент. **Платформы:** Windows 11 host, Guition ESP32-S3 480×480, будущая P4 720×720. **Самое важное требование:** художественный fullscreen background, Nunito/Comfortaa + кириллица, живые данные, [LA-01 RGBA светильник](../03-design/light-action-reference-LA-01.md), собственные widgets, переходы и preview без постоянной перепрошивки.

> **Три принципиально разных механизма:** (1) WYSIWYG editor, (2) YAML/DOM emulator в браузере, (3) **настоящий LVGL renderer**, собранный на ПК. Первые два ускоряют layout, но только третий способен исполнять тот же C/C++ LVGL UI, что будет в native firmware. Даже реальный LVGL на PC не моделирует PSRAM bandwidth и конкретный IPS LCD.

## 1. Матрица инструментов

| Инструмент | Ввод / экспорт | Тип preview | Fonts, images, alpha | Custom widgets, events | Прямой ESPHome YAML | Native C LVGL | Лицензия / риски |
|---|---|---|---|---|---|---|---|
| **[ESPBoards LVGL Designer](https://lvgl.espboards.dev/)** | Drag-and-drop, импорт/экспорт ESPHome LVGL YAML | Browser canvas/редактор, **не native LVGL** | Изображения и asset references; glyph/alpha fidelity проверять на устройстве | В рамках поддерживаемой UI схемы; C++/external components вне редактора | **Да** | Нет | Hosted proprietary service; экспортированный YAML свой, нет подтверждённого headless CLI |
| **[ESPHomeDesigner](https://github.com/koosoli/ESPHomeDesigner)** | UI drag-and-drop, ESPHome YAML или display lambda | Собственный preview, HA-aware, **не native LVGL** | Зависит от режима экспорта, проверять русские glyphs/alpha | LVGL поддержка автором обозначена **Highly Experimental** | **Экспериментально** | Нет | GPL-3.0; возможны несовпадения с актуальной YAML схемой |
| **[ESPHome-LVGL-Simulator](https://github.com/MaxCRRR/ESPHome-LVGL-Simulator)** | ESPHome YAML → браузерный render | **JS model**, не C++ LVGL framebuffer | Fonts via local/Google/CDN, styles, images с оговорками | Многие стандартные виджеты, mouse events; `!lambda` placeholder | **Да, preview** | Нет | MIT; неполная интерпретация YAML/HA и другая rasterization |
| **[LVGL Pro Editor](https://lvgl.io/docs/pro/editor/overview)** | XML source + визуальный Design mode → C | **Real LVGL** runtime preview | Да, полный asset workflow зависит от конфигурации | Custom C widgets, data bindings, animations | Нет | **Да** | Community free для personal/non-commercial; **headless CLI требует paid license** |
| **[EEZ Studio](https://github.com/eez-open/studio)** | `.eez-project` → LVGL C/C++ | Preview/симулятор EEZ; target LVGL надо сверять | Fonts/assets; в native output нужны правильные converters | Events и custom C glue, EEZ Flow опционален | Нет | **Да** | Open-source GPLv3 редактора; при Flow появляется runtime dependency |
| **[SquareLine Studio](https://squareline.io/)** | Drag-and-drop → generated C UI/assets | Design/editor preview | Изображения, fonts, styling | Events/custom actions вокруг generated source | Нет | **Да** | Проприетарный редактор; ограничения лицензии и codegen/CI |
| **[LVGL PC SDL simulator](https://github.com/lvgl/lv_port_pc_vscode)** | Тот же UI C/C++ и LVGL конфиг | **Real LVGL**, SDL display/input | Да, как в выбранной LVGL конфигурации | **Любые** LVGL 9 C widgets | Нет, напрямую YAML не исполняет | **Лучший reuse** | Open-source; надо написать host adapters и mocks |
| Figma / Inkscape / Python Pillow-CairoSVG | Design tokens, SVG/PNG/TTF, композиция | **Статический** 480/720 mockup | Отлично для исходников; не эквивалент render на LCD | Нет runtime interaction | Нет | Assets в обе ветки | Сильный art direction, но неверное ощущение FPS/alpha |
| WebAssembly LVGL / online LVGL demos | C++ code → wasm (зависит от runner) | Может быть **real LVGL** в WASM | Зависит от конкретной сборки | Да, если project loads code | ESPHome YAML напрямую нет | Потенциально да | Нужен version-pinned WASM pipeline и проверка совместимости |
| VS Code extensions / generic UI designer | Разные | Разные | Разные | Разные | Нет универсального WYSIWYG↔ESPHome | IDE над выбранным toolchain | Не считать IDE plugin доказательством faithful preview |

Оценки без аппаратного/визуального PoC приблизительны. «Поддерживает изображения» не означает, что editor точно предсказывает **RGBA на RGB565, premultiplied alpha, dithering, clamping, color management и размер glyph bitmap**. У всех кандидатов отдельно проверить 480×480 и 720×720.

## 2. ESPBoards ESPHome LVGL Designer

Источники: [Designer](https://lvgl.espboards.dev/), [user guide](https://lvgl.espboards.dev/help/user-guide/), [import/export](https://lvgl.espboards.dev/help/guide/add-lvgl-design/), [terms](https://lvgl.espboards.dev/terms/).

**Роль:** визуальное авторство **именно ESPHome `lvgl:` YAML**, что отличает его от EEZ/SquareLine. Drag-and-drop, multiple screens/pages, базовые layout-системы, import existing YAML и export `lvgl:` tree с image references делают его первым кандидатом для архитектуры A. Экспортированный YAML хранить в Git и считать исходником; hosted designer — временный интерфейс.

**Проверки на RH-01:** импорт нашего реального YAML; заменить background на комнатный 480 PNG; задать координаты clock/weather/temperature; добавить пару lamp states и invisible hit target; export → `esphome config` без потери substitutions, package includes, glyphs, on_click/HA actions. Применить **round-trip test**: экспорт → ручной patch → повторный импорт → повторный экспорт → `git diff`. Выявить, какие нестандартные CSS/LVGL-атрибуты редактор молча теряет.

**Слабые стороны/риски:** проприетарный hosted tooling и отсутствие документированного CLI; проект редактора нельзя гарантированно воспроизвести без cloud; не обещать 100% поддержку ESPHome `!lambda`, external C++ и всех текущих LVGL widgets; preview не является renderer'ом целевого прошивочного кода. Хранить экспорт YAML и master assets локально, секреты HA никогда не вставлять в облачный editor.

## 3. ESPHomeDesigner (koosoli)

Источник: [README, лицензия и исходники](https://github.com/koosoli/ESPHomeDesigner).

**Роль:** open-source визуальный редактор, способный показывать HA entity values и генерировать ESPHome display lambda либо LVGL YAML. Это не две эквивалентные реализации: **display lambda drawing не равен LVGL object tree**, поэтому выбирать режим LVGL явно. Официальное README помечает LVGL integration как **Highly Experimental** и отмечает требования к ESP32-S3/PSRAM.

**Проверить:** последнюю release/commit/activity на дату фактического PoC, работает ли на Windows через браузер или отдельную сборку, корректны ли imports substitutions, includes, fonts, RGBA lamp, touch events, `page.show`, HA state mocks. Сравнить два последовательных export на детерминированность. Не делать основной source-of-truth из нестабильного формата проекта до проверки.

**Сильная сторона:** прямой HA-aware preview и публичный исходный код. **Недостаток:** экспериментальная LVGL ветка и риск расхождения с ESPHome 2026.10.x schema. Generated code/конфиги проверять отдельно; GPL редактора не следует автоматически отождествлять с лицензированием собственных YAML-файлов — посмотреть конкретные условия.

## 4. ESPHome-LVGL-Simulator (MaxCRRR)

Источник: [GitHub README](https://github.com/MaxCRRR/ESPHome-LVGL-Simulator). Репозиторий описывает браузерный JavaScript preview для ESPHome YAML, включая `substitutions`, named colors, themes, pages, flex/grid, buttons, switches, arcs, meters, lines, widgets, navigation, fonts; `!lambda` отображается placeholder (`~sensor_id~`), некоторые значения генерируются тестовыми.

**Очень важное ограничение:** renderer не использует ESPHome C++ + собственно LVGL framebuffer. Browser layout/anti-aliasing ≠ LVGL 9, особенно для кириллицы, прозрачности, glow, clipping, frame timing. Поэтому **никаких pixel-perfect acceptance screenshots** из этого инструмента. Это быстрое средство итерации, не hardware oracle и не тест фактического HA native API.

**Local Windows workflow (если клонирован репозиторий):**

```powershell
git clone https://github.com/MaxCRRR/ESPHome-LVGL-Simulator.git
cd ESPHome-LVGL-Simulator
py -3 -m http.server 8080
# http://localhost:8080/index.html
```

Открыть browser, вставить/импортировать RH-01 YAML и нажать Render. Сверить поддерживаемые directives. Дополнительный AI analysis API key **не нужен** для render и для проекта FormaPanel не требуется. Не передавать HA tokens, secrets и приватные конфигурации во внешнюю облачную среду.

**Рекомендация:** fast loop: YAML → browser preview → `esphome config` → compile → реальный экран. Не делать simulator screenshot блокирующим CI gate, пока не ясно, какая часть widgets/alpha интерпретирована faithfully.

## 5. LVGL Pro Editor (официальный XML + real runtime)

Источники: [Editor](https://lvgl.io/docs/pro/editor/overview), [CLI](https://lvgl.io/docs/pro/cli), [license](https://lvgl.io/docs/pro/editor/license), [pricing](https://lvgl.io/pro/pricing).

**Возможности:** XML source files, Code + Design режимы, real LVGL live preview, generated C, custom C widgets, animations, bindings, UI testing. Для родного LVGL это очень сильный процесс:

```text
ui/native/screens/rh01.xml + widgets/lamp.xml + generated assets
   → LVGL Pro visual+real preview
   → C sources
   → SAME UI C integrated in host SDL and native ESP-IDF firmware
```

**Лицензирование:** Community Editor бесплатен для личного/некоммерческого использования; **CLI** (`lvglpro generate/validate/run-all-tests/screenshot`) доступен только по коммерческому лицензированию Product/Platform и требует токен. На [pricing](https://lvgl.io/pro/pricing) фигурирует Product tier **$20 000/product** (на дату исследования; стоимость может измениться). Не строить обязательный бесплатный GitHub Actions вокруг CLI. Выгруженные C источники хранить в Git, чтобы не зависеть от CI CLI. Не выкладывать license token.

**Практический тест:** импорт двух RGBA lamp states, placement в 480×480, mock values (clock 23:59, температура отрицательная/положительная, влажность, CO₂), binding/state changes, custom C widget и повторяемый экспорт. Проверить фактическую работу editor на Windows, а не объявлять её доказанной по документации.

## 6. EEZ Studio

Источник: [source/repository](https://github.com/eez-open/studio), [FAQ](https://github.com/eez-open/studio/wiki/FAQ).

**Что использовать:** «LVGL» проект с генерацией C/C++, `ui_init()`, assets, widgets, local runtime functions; приложение и callbacks хранить **вне** generated code, чтобы re-export не затирал бизнес-логику.

**Два режима нельзя смешивать:**
- *EEZ native LVGL code export:* генерация C UI, собственные actions/state handlers; независимость от EEZ Flow runtime (при правильной конфигурации).
- *EEZ Flow:* visual behavior/rule engine; может потребовать EEZ runtime и увеличивает размер/сложность прошивки. Проверять RAM/Flash, lifecycle событий, возможности отладки. Нет автоматической трансляции ни первого, ни второго в **ESPHome YAML**.

Плюсы: бесплатный/open-source editor, широкая кастомизация UI, работа с собственными ресурсами, C export. Риски: precision preview зависит от fonts/config, C custom events требуют glue, CI generation не считать штатным до воспроизводимого headless теста; совместимость конкретной LVGL 9.x версии подтверждать сборкой.

## 7. SquareLine Studio

Источники: [сайт](https://squareline.io/), [changelog](https://docs.squareline.io/docs/miscellanos/changelog/), [export docs](https://docs.vision.squareline.io/docs/export/).

В релизной истории за 2026 зафиксирован **1.6.2 (10.08.2026)** с LVGL 9.5 / SVG widget support (сверить target LVGL и local installer при PoC); 1.6.1 добавляла screenshot export. Достоинства — зрелый drag-and-drop UI, styles, fonts, exported C/C++ assets. Недостатки — отдельный проект/проприетарные условия, не ESPHome YAML, ручной контроль generated source при version change, desktop preview ≠ hardware. Не закладывать автоматическую регенерацию в CI без документированного licensable CLI.

## 8. LVGL PC simulator (SDL; официальная основа)

Источники: [lv_port_pc_vscode](https://github.com/lvgl/lv_port_pc_vscode), [LVGL PC integration](https://docs.lvgl.io/master/details/integration/pc/index.html). Здесь **настоящий LVGL**, но без ESP32 framebuffer driver. Можно запускать тот же `ui_core`, что в native IDF:

```text
                             ┌── SDL host (Windows/Linux, mouse → touch)
ui/core [pure LVGL C/C++] ───┤
                             └── ESP-IDF + board driver + GT911
```

Для совпадения картинки нужно pin одной версии LVGL, те же font bitmaps, images, `LV_COLOR_DEPTH`/ARGB settings, gamma/opacity, clipping и clock mock data. Слой событий и состояние UI должны быть разделены от transport. **Не использовать скриншот SDL как эквивалент LCD:** GPU/IPS RGB565 quantization, PSRAM/latency и input hardware отличаются.

Официальный starter — CMake/SDL; на Windows возможны VS Code + CMake + Ninja + vcpkg (вариант MSVC или MinGW должен быть один). Для CI Linux + `xvfb` запускает тот же host binary и делает screenshots после добавления собственного FormaPanel screenshot harness.

С ESPHome **нельзя** взять YAML и скомпилировать его в этот симулятор без отдельного ESPHome codegen/host adaptation. Реальное reuse UI достигается только для native C/C++ path; это важнейший tradeoff.

## 9. Figma / Inkscape / WASM / инструменты второго эшелона

- **Figma:** хорош для прототипов, расположения, design tokens, фоновых вариантов, но нельзя гарантировать прямой Figma→ESPHome YAML. У LVGL Pro есть собственный Figma-related workflow; совместимость generated C, лицензия и переиспользование требуют отдельного PoC. Figma screenshot — *reference*, не работающий MCU.
- **Inkscape + Pillow/CairoSVG:** правильные masters SVG/PNG и offline преобразование, подготовка RGB565/dithering/alpha mask; собственный `tools/render_assets.py` в FormaPanel уже существует. Проверить несоответствие CairoSVG и LVGL text rendering, поэтому для финального layout все значения отрисовываются в runtime.
- **LVGL WASM/web demos:** если WebAssembly runner реально компилирует pinned LVGL 9 + `ui_core`, может давать faithful render engine по отношению к LVGL логике. Но это **отдельная интеграция**, не найден универсальный загрузчик ESPHome YAML; не заменять host SDL без сравнительного теста. Зафиксировать исходник WASM port, version, сборку.
- **VS Code plugins / LVGL XML Editor:** редактор файлов, диагностика XML/YAML и code completion не обязательно имеют LVGL engine. Противопоставлять визуальный editor и runtime simulator корректнее, чем названия расширений IDE.
- **Wokwi/симуляция ESP32:** может помогать железо/протоколам, но нельзя предполагать поддержку конкретного RGB ST7701+GT911 480×480 и достоверной UI-производительности без верификации.

## 10. Сравнение именно под FormaPanel RH-01/LA-01

| Тестовое требование | ESPBoards | ESPHomeDesigner | ESPHome-LVGL-Simulator | LVGL Pro | EEZ/SquareLine | Native SDL |
|---|---|---|---|---|---|---|
| Без перепрошивки меняем геометрию RH-01 | Да | Да | Да, но текстовое YAML → Render | Да | Да | Да после rebuild/hot-run |
| Собственный фон (не картинка из HA) | Да, asset ref | Проверить | Проверить local resource loading | Да | Да | Да |
| Реальный render кириллицы 480 RGB565 | Нет | Нет | Нет | LVGL близко, LCD отдельно | Studio зависит от runtime | **Да, с matching color/font config** |
| Alpha LA-01, градиент вверх | Предварительное | Предварительное | Предварительное | LVGL preview | LVGL target build | **Тот же LVGL bitmap code** |
| Любой custom C widget | Нет | Нет | Нет | Да | Нужно native интеграция | **Да** |
| Напрямую повторно используемый ESPHome YAML | **Да** | Экспериментально | **Да, на входе** | **Нет** | **Нет** | **Нет** |
| HA mock states, touch | Частично | HA-aware | Mock + events, lambda placeholders | Bindings + mock | Events/code | **Пишем mock state adapter** |
| Нет vendor lock-in | YAML сохраняется, сервис закрытый | Open source | Open source | XML+C, но authoring tool licensed | EEZ open/SquareLine closed | **Полный контроль** |

## 11. Порядок проверки инструментов

1. **ESPHome lane:** import/export минимального `RH-01` в ESPBoards, сравнить YAML; затем открыть **тот же файл** в ESPHome-LVGL-Simulator, проверить pages/text, фон и glow; на следующих итерациях попробовать ESPHomeDesigner. В Git храним только YAML/assets, не облачную копию проекта.
2. **Native lane:** тот же RH-01 собрать в LVGL Pro (проверить свободный tier), EEZ и при необходимости SquareLine, экспортировать generated C; скомпилировать **один `ui_core`** в SDL и IDF. Проверить прохождение custom lamp widget без дублирования логики.
3. **Финальный gate:** физическая Guition, реальная alpha с наименее удачным тёмным и светлым фоном, 3 комнаты/одна сетка, время обновления и касание, RAM/PSRAM/FPS. Browser screenshots не засчитывать как hardware proof.

Практические команды, policy source-of-truth и CI: [build-preview workflows](build-preview-workflows.md). Критерии: [RH-01/LA-01 A/B](../06-validation/rh01-platform-ab-test.md). Источники и границы проверенности: [реестр](research-source-register-2026-10.md).
