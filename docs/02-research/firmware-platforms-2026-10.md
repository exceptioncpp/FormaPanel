# Базы прошивки FormaPanel — техническое сравнение (29.10.2026)

**Статус:** research / candidate evaluation, не архитектурное решение и не измерение на железе. **Актуально на:** 2026-10-29. **Цель:** 5 локальных панелей Home Assistant на Guition ESP32-S3-4848S040 (4″, 480×480, touch); отдельно будущий ESP32-P4 720×720, плата не выбрана.

Связанные спецификации: [RH-01](../03-design/room-home-reference-RH-01.md), [LA-01](../03-design/light-action-reference-LA-01.md), [железо](../04-architecture/hardware.md), [HA contract](../04-architecture/ha-contract.md), [ADR-0001](../04-architecture/adr/0001-native-lvgl.md). Это исследование не отменяет дизайн-решений. В частности, на главной жилой странице **полноэкранная фотография + независимые живые числовые слои + RGBA-светильник**, без карточного UI.

## Система статусов и приоритетов

- **[official]**: прямо задокументированная функциональность официального проекта/компонента.
- **[community]**: исходники/демо сообщества; не гарантия на нашей ревизии.
- **[proposed]**: проектная архитектура, требующая реализации.
- **[untested]**: ещё нет воспроизводимой сборки/измерения FormaPanel.
- **[risk]**: несовместимость, лицензия, память или поддержка могут оказаться блокерами.

Главные критерии: собственные фоновые изображения, точная типографика с кириллицей, нестандартные LVGL-виджеты/анимации, повторное использование UI на 5 панелях, достоверный preview **до** flash, офлайн-подключение к HA, управляемый ресурсный бюджет. «LVGL 9 совместим» означает лишь совместимость программного интерфейса, а **не** подтверждённый вывод изображения на конкретном S3/P4.

## 1. Сводная матрица

| Стек | Свои фоны, PNG/alpha, TTF | Custom LVGL/анимация | Home Assistant | Реальный LVGL preview с тем же UI | Guition S3 | Основные риски | Решение |
|---|---|---|---|---|---|---|---|
| **ESPHome + LVGL 9, ESP-IDF** | **Да** с конвертацией assets и контролем памяти | YAML-подмножество; C++ через lambdas/external components | **native API**, стандартные состояния и actions | **Нет** штатного общего host-runtime для YAML; браузерные preview приблизительны | **[official]** `mipi_rgb model: GUITION-4848S040`; touch зависит от разводки | API/YAML limits, alpha/RGB565, memory/PSRAM, неэквивалентность превью | **Кандидат A** |
| **Native ESP-IDF + LVGL 9** | **Да**, полный LVGL API | **Полный C/C++ LVGL** (custom draw, canvas, events) | Реализовать MQTT/HA bridge и OTA | **Да**: один UI C/C++ с LVGL SDL на PC + firmware | [proposed] собственный board layer, `esp_lcd`, GT911 | Объём системного кода и времени разработки, реальный порт платы | **Кандидат B** |
| Arduino-ESP32 + LVGL 9 | Да | Полный LVGL C/C++ | MQTT / собственный bridge | Да, если выделить независимый UI core | Vendor demos на LVGL 8.x не являются готовым LVGL 9 портом | Additional core + IDF internals, версии, DMA/PSRAM | Не основной |
| PlatformIO + ESP-IDF/Arduino | = выбранному framework | = framework | = framework | = framework | = framework | Это **сборочная среда**, не отдельный firmware stack | Не сравнивать как прошивку |
| openHASP | JSONL/objects, ресурсы в пределах runtime | В рамках декларативного объекта/скриптов, не full native LVGL C | MQTT (обычно HA automation/integration) | Нужен отдельный path | Проверить конкретный board profile/revision | Система объектов и UX не совпадают с RH-01, ограничения бинарных assets | Reference/альтернатива |
| Tessera / homeassistant_espscreen | В рамках manager/editor и runtime | Ограничено API проекта; исходники требуют анализа | HA через собственную инфраструктуру | Собственный editor, не тождественен shared LVGL SDL | Community support, проверять версии | Менеджер/конфигурация, зависимость от runtime, отступление от UI-контракта | Reference |
| EspControl / готовые ESPHome dashboards | Да, если исходники доступны | Зависит от выбранного проекта | Обычно ESPHome native API | Как у ESPHome | Есть community примеры под 4848S040 | Их карточная композиция не соответствует RH-01; интеграционный долг | Примеры, не foundation |
| Заводская Guition Arduino LVGL 8.3.9 | Изображения/анимация демонстрируются | Полный C UI, но старый LVGL | В архиве внешний weather API, нет готового HA-контракта | Собственная среда/портирование | [community/vendor] для близкой модели | 8.3→9, право на перераспространение ассетов, SDK quality | Технический референс |
| Zephyr + LVGL | Да | Полный LVGL | MQTT/custom | Возможен отдельный host core | [untested] требуется board/display port | Большой объём board/HA работ | Наблюдать |
| Apache NuttX + LVGL | Да | Полный LVGL | MQTT/custom | Возможен | [untested] board port | Часть P4 graphics acceleration может быть не поддержана | Наблюдать |
| Mongoose OS + LVGL | Требует интеграции | Через собственный порт | MQTT | Самостоятельно | [untested] first-class S3 RGB profile не обнаружен | Порт дисплея и LVGL поверх IoT framework | Не включать в PoC |

**Не путать платформу, UI редактор и готовую тему.** ESPBoards/EEZ/SquareLine — средства authoring, не прошивки. RemoteWebView/Chromium server — принципиально иная, серверозависимая архитектура, не нативный LVGL.

## 2. ESPHome + LVGL 9 + ESP-IDF

**[official]** [ESPHome LVGL](https://esphome.io/components/lvgl/) строит LVGL UI из YAML. В ESPHome [`mipi_rgb`](https://esphome.io/components/display/mipi_rgb/) есть `GUITION-4848S040`, а [device listing](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/) описывает ESP32-S3, 480×480, ST7701S/GT911 и распространённую конфигурацию 16 MB flash + 8 MB PSRAM. Эти параметры **не проверены на имеющейся физической ревизии**. [ESPHome API](https://esphome.io/components/api/) обеспечивает обмен с HA без отдельного MQTT-сервера.

**Кастомизация.** Слои изображения (`image:`), кастомные шрифты (`font:` и glyph subset), LVGL widgets, alignment, styles, background, opacity, actions, pages, animations входят в рабочую модель. Для русского текста зафиксировать Unicode-набор кириллицы, цифр, `°`, `%`, `₂`, единицы измерения; проверить Nunito/Comfortaa против утверждённого RH-01. Динамические метрики и свет никогда не запекать в фон. Для LA-01 готовить два одинаково позиционированных прозрачных RGBA-спрайта; проверить поддерживаемый ESPHome формат изображения и реальное alpha blending на RGB565, а не предполагать, что desktop PNG декодируется напрямую на устройстве. Документация: [images](https://esphome.io/components/image/), [fonts](https://esphome.io/components/font/).

**Escape hatch:** `lambda`/custom C++/external components дают доступ к дополнительному LVGL API, но код становится менее видимым ESPBoards/ESPHomeDesigner и менее переносимым при обновлении ESPHome. Не предполагать, что любой `lv_obj_class_t` можно описать простым YAML widget.

**Плюсы:** native HA API, Wi-Fi, OTA, logging, encrypted API, YAML packages/substitutions для living/bedroom/office, маленький объём инфраструктурного кода; официальная модель дисплея. **Минусы:** declarative subset не эквивалентен полному C API; меньше прямого контроля над `esp_lcd`, DMA, RGB timing, heap placement и scheduling; браузерный preview не является эталоном LVGL. Производительность в этой конфигурации **не измерена**.

**Практическая архитектура [proposed]:** `boards/guition-s3-480.yaml` + `packages/system/{network,display,touch,api,ota}.yaml` + `packages/ui/{fonts,assets,theme,rh01}.yaml` + `panels/{living,bedroom,office,bathroom,hallway}.yaml`; HA entity mapping в room profile, secrets вне git. Блок hardware init не копировать из случайной статьи, начать с официального preset и выяснить его совместимость.

## 3. Native ESP-IDF + LVGL 9

**[official]** [ESP-IDF](https://github.com/espressif/esp-idf/releases) предоставляет `esp_lcd`, драйверы, PSRAM/DMA, FreeRTOS, networking и OTA; [LVGL](https://github.com/lvgl/lvgl) — renderer, native objects/events/animations. [`esp_lvgl_port`](https://components.espressif.com/components/espressif/esp_lvgl_port) и `esp_lcd_touch` уменьшают объём glue-кода. Для конкретного Guition **не найдено подтверждённого в FormaPanel board package**, поэтому wiring, RGB timings, ST7701 initialization, backlight GPIO и touch calibration — самостоятельная задача.

**Кастомизация:** custom `lv_obj_class_t`, drawing/alpha/canvas, animated images, input devices, raw LVGL C/C++, дополнительные библиотеки и память на уровне firmware. Можно делить один `ui_core` между микроконтроллером и LVGL PC SDL host, оставив зависимости `esp_*` строго в `board_guition` и `ha_bridge`. Это **самый достоверный preview без прошивки**, хотя цветопередача физического LCD, PSRAM latency и touch hardware всё равно проверяются отдельно.

**Home Assistant:** не считать ESPHome native API бесплатной библиотекой для native IDF. Реалистичный вариант — MQTT retained state/discovery + команды и ack, либо собственный HA WebSocket/REST bridge. Не отправлять сетевую операцию из LVGL event callback блокирующим образом. Проработать TLS/auth, reconnect, OTA, mDNS, provisioning, stale-state/last-known-value, time sync; native path гораздо дороже по обслуживанию.

**ESP32-P4:** native IDF открывает доступ к PPA/2D-DMA и более тонкому управлению графикой; при этом P4 hardware profile **ещё не выбран** и переносить S3 display driver без доказательств нельзя. P4 Wi-Fi/network coprocessor, MIPI-DSI vs RGB, framebuffers, PSRAM и panel/touch pins требуют собственного PoC.

**Плюсы:** максимальная визуальная свобода; контролируемая память; реальные host LVGL rendering tests; самый прямой путь к P4 graphics. **Минусы:** собственная аппаратная и HA-инфраструктура, OTA/security; выше стоимость поддержки пяти панелей. **Кандидат B — не утверждённый победитель.**

## 4. Arduino / PlatformIO / другие RTOS

- **Arduino + LVGL:** пригоден, когда нужно быстро поднять оригинальный demo C и исследовать animation timing; полноценный UI и SDL-переиспользование возможны. Но рост требований к RGB DMA, PSRAM и P4 приводит к прямому использованию IDF API поверх Arduino. Заводской LVGL 8.3.9 нельзя просто линковать с LVGL 9 без миграции.
- **PlatformIO:** `framework=espidf` или `framework=arduino`, pin dependencies и CI удобны; это build/tooling, а не новая UI architecture. Для нативного эксперимента сначала использовать `idf.py`/CMake/Ninja: меньше уровней несовместимости. [Документация](https://docs.platformio.org/en/latest/platforms/espressif32.html).
- **openHASP:** для JSONL MQTT панелей и стандартных UI объектов; ограничения сложного авторского художественного RH-01 проверять отдельно; не смешивать с ESPHome YAML. [Проект](https://www.openhasp.com/).
- **Tessera / EspControl / готовые dashboard UI:** ценны паттернами переходов, вложенными экранами, responsive handling, OTA и HA, но не предполагаются свободно переносимыми «темами». Сверять source license, build instructions и конкретную board revision: [Tessera](https://github.com/MaxGramser/homeassistant_espscreen), [EspControl](https://jtenniswood.github.io/espcontrol/screens/4848s040), [Guition examples](references.md).
- **Zephyr/NuttX/Mongoose OS:** потенциальные alternative SDK, но для строго ESP32+HA/LVGL задача board display/HA интеграции не окупается. [Zephyr ESP32-P4 board](https://github.com/zephyrproject-rtos/zephyr/tree/main/boards/espressif/esp32p4_function_ev_board), [NuttX P4 support](https://nuttx.apache.org/docs/latest/platforms/risc-v/esp32p4/index.html), [Mongoose OS](https://mongoose-os.com/docs/README.md).

## 5. Ресурсы: без ложного benchmark

| Буфер | RGB565 (2 B/pixel) | Два framebuffer | ARGB8888 (4 B/pixel, один) |
|---|---:|---:|---:|
| 480×480 | 460 800 B = 450 KiB | 900 KiB | 900 KiB |
| 720×720 | 1 036 800 B ≈ 1013 KiB | ≈ 2025 KiB | ≈ 2025 KiB |

Это **не общий расход RAM**. Добавить LVGL draw buffers, full-screen decoded background(s), alpha overlays, glyph cache, application heap, Wi-Fi/TLS, FreeRTOS stacks, DMA-friendly internal RAM. Цвет RGB565 framebuffer не исключает 8-битную alpha исходной картинки: ограничение определяется decoder/converter, конфигурацией LVGL и pipeline смешивания. Предварительно оценить dithering/banding тёмных градиентов, RAM allocation failure и полные переходы. Таблицы FPS без запуска на Guition не создавать.

**Лицензии:** LVGL — MIT ([license](https://lvgl.io/docs/open/introduction/license)), ESP-IDF — преимущественно Apache-2.0 с зависимостями ([репозиторий](https://github.com/espressif/esp-idf)); ESPHome включает компоненты с различными лицензиями — юридические выводы делать по релевантным LICENSE/SPDX для конкретной версии, а не по одному файлу случайного форка. Arduino core, visual editor и vendor artwork имеют отдельные условия. FormaPanel пока без собственной выбранной LICENSE ([legal](../07-legal/licensing.md)).

## 6. Версии и воспроизводимость

На дату контрольной сверки:

| Инструмент | Проверенный источник | Что фиксировать для эксперимента |
|---|---|---|
| ESPHome | [releases](https://github.com/esphome/esphome/releases), выпуск **2026.10.0** | **`esphome==2026.10.0`** (не `2026.10.1`: в релизах на 29.10 эта версия не подтверждена) |
| ESP-IDF | [releases](https://github.com/espressif/esp-idf/releases), **v6.1** | тег и commit; compatibility с `esp_lvgl_port` проверить сборкой |
| LVGL | [releases](https://github.com/lvgl/lvgl/releases) | конкретный 9.x git tag/commit, **пока не зафиксирован** |
| esp_lvgl_port | [component registry](https://components.espressif.com/components/espressif/esp_lvgl_port) | совместимый pin после проверки, не `^latest` |
| Python asset tools | [requirements](../../tools/requirements.txt) | lock после выбора среды, локальная и CI одна версия |
| hardware | [Guition profile](https://esphome.io/components/display/mipi_rgb/) | фото платы, full boot log, timings и actual PSRAM |

**Важное исправление относительно первоначального исследовательского черновика:** не закладывать `esphome==2026.10.1` до фактической публикации и проверки этого релиза.

## 7. Взвешенный выбор (оценки гипотезы, не benchmark)

Шкала 1–5; вес каждого критерия суммарно 100%. Результат = Σ(оценка × вес)/100. Ранжирование выражает **цели проекта**, не объективный уровень SDK.

| Критерий | Вес | ESPHome | Native ESP-IDF |
|---|---:|---:|---:|
| UI свобода/свои custom widgets/эффекты | 25 | 4 | 5 |
| Достоверный desktop preview и reuse UI | 20 | 2 | 5 |
| Интеграция HA / offline state / OTA | 15 | 5 | 2 |
| Готовность платы Guition S3 | 15 | 5 | 3 |
| Контроль FPS/PSRAM/DMA | 10 | 3 | 5 |
| Стоимость реализации и поддержки | 10 | 5 | 2 |
| Потенциал P4 720 | 5 | 3 | 5 |
| **Сумма / 5** | **100** | **3,80** | **4,25** |

Native лидирует при специально высоком весе custom UI/preview, но это **не release decision**: выше риск board bring-up и HA architecture. Если вес HA/срока MVP поднять, ESPHome станет рациональнее. Если RH-01 реализуется в ESPHome без C++ обходов и визуальных артефактов, нет причин автоматически переходить на native.

## 8. Условия решения

**Выбрать ESPHome**, если exact revision выводит 480×480 и touch без сомнительных драйверов, RH-01/LA-01 реализуются в YAML, корректны кириллица и alpha, UI не подлагивает, OTA/HA работает устойчиво, а несоответствие browser preview нивелируется аппаратной проверкой.

**Выбрать native IDF**, если нужны custom C widget pipelines или более сложное animation/rendering, ESPHome YAML оказывается слишком ограниченным, browser preview слишком далёк от pixel-level fidelity, для S3 важен тонкий контроль RGB/PSRAM или P4 становится приоритетной платформой.

**Проверить по общему протоколу**, прежде чем принимать ADR: [RH-01 A/B тест](../06-validation/rh01-platform-ab-test.md). Отдельный документ по инструментам: [визуальные редакторы](lvgl-visual-tools-2026-10.md); сценарии разработки: [build-preview](build-preview-workflows.md).

## Первоисточники

[ESPHome LVGL](https://esphome.io/components/lvgl/) · [ESPHome MIPI RGB](https://esphome.io/components/display/mipi_rgb/) · [ESPHome Guition device](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/) · [ESPHome API](https://esphome.io/components/api/) · [ESPHome fonts](https://esphome.io/components/font/) · [ESPHome releases](https://github.com/esphome/esphome/releases) · [ESP-IDF releases](https://github.com/espressif/esp-idf/releases) · [Espressif LVGL port](https://components.espressif.com/components/espressif/esp_lvgl_port) · [LVGL](https://github.com/lvgl/lvgl) · [PlatformIO](https://docs.platformio.org/en/latest/platforms/espressif32.html) · [NuttX P4](https://nuttx.apache.org/docs/latest/platforms/risc-v/esp32p4/index.html). Полный проверочный реестр: [sources](research-source-register-2026-10.md).
