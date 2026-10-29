# RH-01 / LA-01 — сравнительный технический PoC ESPHome vs ESP-IDF

**Статус:** план эксперимента, не test report. **Дата:** 2026-10-29. **Обе прошивки пока не собраны и на реальной панели не измерены.**

Связанные документы: [approved RH-01](../03-design/room-home-reference-RH-01.md), [approved LA-01](../03-design/light-action-reference-LA-01.md), [архитектурные кандидаты](../02-research/firmware-platforms-2026-10.md), [предпросмотр](../02-research/lvgl-visual-tools-2026-10.md), [build и CI](../02-research/build-preview-workflows.md), [performance](performance.md).

## 1. Цель

Принять основанное на данных решение для Guition ESP32-S3-4848S040, сравнив две **сопоставимые** реализации того же approved UI:

- **A:** ESPHome 2026.10.0 + LVGL 9 через ESP-IDF + ESPHome native HA API.
- **B:** native ESP-IDF v6.1 + LVGL 9 + `esp_lcd`/`esp_lvgl_port`, mock HA на первом этапе; затем MQTT/bridge.
- **Отдельно:** сравнить качество authoring и предпросмотра без устройства (ESPBoards/ESPHomeDesigner/ESPHome-LVGL-Simulator vs LVGL Pro/EEZ/SquareLine/SDL).
- **Не цель:** одновременно довести до production две ветки или менять approved RH-01/LA-01 ради программных удобств.

## 2. До эксперимента: аппаратная идентификация P0

**[open]** Точная версия панели, используемые framebuffer timings, распиновка дисплея и GT911 ещё не подтверждены измерениями FormaPanel.

Потребуются:

| Входные данные | Источник | Зачем |
|---|---|---|
| Фотографии обеих сторон PCB, маркировка S3/PSRAM/Flash/LCD/touch IC | Реальное устройство | Сопоставить с ESPHome preset и vendor revision |
| Serial boot log при power-on и warm reset | USB-UART | Pin/errors, flash/PSRAM size/mode, touch init |
| Factory flash backup + flash partitions, когда разрешено и возможно | esptool | Безопасный rollback и анализ vendor-init |
| Версия платы и конфигурация дисплея | datasheet/vendor archive/physical | RGB timing, ST7701 init, backlight polarity |
| Touch raw map по четырём углам/центру | Runtime touch test | Orientation, offsets, X/Y swap, debounce |
| Wi-Fi/OTA и recovery mechanism | Runtime | Устойчивый эксперимент без brick |
| Фактическая PSRAM, свободная internal heap, большой allocatable block | Logs | Двойные буферы, картинки, память |
| Фото IPS при RGB stripes, 1px сетке, gradient, full black | Device photos | Banding, geometry, bleed, color |

Не утверждать pin compatibility с [`GUITION-4848S040`](https://esphome.io/components/display/mipi_rgb/) пока не проверены конкретная ревизия и touch pins. Указанный preset является **официальной отправной точкой**, не фактом успешной прошивки FormaPanel.

## 3. Один набор исходных данных для обеих веток

Строго одинаковые:

- **Canvas:** 480×480. Три профиля living/bedroom/office с **одинаковыми координатами** и разными фоновыми изображениями. Не добавлять карточки, подписей комнат и дату.
- **Фон:** один выбранный approved-looking художественный 480×480 background для A/B; позднее протестировать другие контрастные backgrounds.
- **Часы:** крупные live `HH:MM`, включить экстремальный `23:59`.
- **Погода:** наружная температура и условный ветер в верхней/погодной зоне, моковые иконки/состояния.
- **Климат:** температура крупно слева, RH% и CO₂ ppm меньшими цифрами столбцом справа. Пустые/недоступные значения не должны сдвигать композицию.
- **LA-01:** утверждённый контурный *подвесной полукупол*, слабый halo, **alpha-gradient wire fades upward**, одинаковая RGBA canvas/offset для off и on; отдельный invisible touch target ~9–10 mm физически. Состояния off/on/pending/unavailable.
- **Шрифты:** один набор Nunito или Comfortaa (выбор ещё не финализирован), одинаковый source TTF/OTF, size, glyph subset, BPP; русский текст на secondary test screen, знаки `°`, `%`, `₂`, `–`, `−`.
- **Mock states:** стабильная запись synthetic events с seed, чтобы обе прошивки получали одинаковый сценарий; без внешней погоды и API.
- **Действия:** light tap переводит в `pending`; только подтверждённая смена HA mock state переводит в `on`; отказ/timeout показывает unavailable/error, а не ложное подтверждение.

### Предлагаемый fixture

```yaml
# docs-only illustration, NOT an ESPHome panel configuration
timestamp: "2026-10-29T20:00:00+03:00"
room: living
clock: "23:59"
weather: cloudy
outside_celsius: -6.4
wind_mps: 7.1
inside_celsius: 23.4
relative_humidity_percent: 43
co2_ppm: 780
light:
  initial: off
  sequence: [tap, pending, confirmed_on, pending, confirmed_off, unavailable]
```

Добавить как версионируемый тестовый mock лишь после выбора adapter format для обеих веток.

## 4. Фазы испытаний

| Фаза | ESPHome A | Native B | Gate |
|---|---|---|---|
| S0: bare board | Display preset, GT911, backlight/OTA | `esp_lcd` + ST7701 + GT911 | Все пиксели, touch and recovery |
| S1: static RH-01 | ESPHome YAML image/fonts/labels | LVGL C UI, SDL host | Визуальная композиция совпадает |
| S2: RGBA LA-01 | Two sprites + invisible tap | Same RGBA inputs + LVGL image widgets | Нет black box, одинаковый offset, glow и fade |
| S3: dynamic state | ESPHome components mock | Host mock adapter | Никаких сдвигов layout, off/pending/on |
| S4: 3 pages + navigation | ESPHome pages, effects | LVGL scene navigation | Touch event correctness + smooth transitions |
| S5: HA | Native ESPHome API | MQTT/custom bridge | State/update/ack/reconnect consistent |
| S6: stability | 24h idle + switching stress | Аналогично | Нет fragmentation/leaks/watchdog |
| S7: developer UX | GUI editor round-trip and JS preview | LVGL Pro/EEZ → C → SDL | Комфортная итерация, повторно используемый исходник |

### Проверки светильника LA-01

1. Проверить PNG на шахматной подложке, минимум трёх фонах (тёмный, светлый, контрастный).
2. Проверить, что transparent pixels действительно transparent, **не** prefilled black; для `on` glow мягкий, для `off` **нет тёплого halo**.
3. Провод визуально затухает наверх до alpha=0; форма — **не** обычная лампочка и не физически непрозрачная люстра.
4. `off`/`on` имеют одинаковое положение и размер; при переключении ничего не подпрыгивает.
5. Проверить premultiplied/straight alpha и цвет по GPU screenshot/IPS фото. RGB565 blending может давать banding, решить dithering на стадии asset conversion.
6. Touch target независим от отрисованной alpha-маски, удобен на физическом 4″ экране.
7. При недоступности HA не имитировать достоверное `on`.

## 5. Протокол измерений (одинаковый для A/B)

| Метрика | Как собрать | Критерий |
|---|---|---|
| Build/revision | git SHA, ESPHome/IDF/LVGL SHA, firmware ELF/bin, hardware photo | Полная воспроизводимость |
| Flash footprint | `size`, linker map, assets sizes | В пределах partitions, запас документирован |
| Free internal heap / largest block | periodic log + после navigation/stress | Нет монотонного снижения и критической фрагментации |
| Free PSRAM / allocated framebuffer(s) | allocator instrumentation/logs | Запас для texture+network stacks |
| Fullscreen redraw p50/p95/p99 | LVGL instrumentation, high-res timestamps на target | Порог после первого device baseline |
| Partial repaint (clock/sensor) | Static page + one label change | Нет full-screen repaint без причины |
| Transition 480×480 | 2–3 page transitions with complex background | Нет заметного tearing/freeze; frame time measured |
| Touch → first visual feedback p50/p95/p99 | Event timestamp → actual render/flush timing; при возможности video | **Начальный UX ориентир** <150–200 ms, требует проверки |
| HA tap → confirmed state | mock+real HA timestamps | Никаких optimistic false confirmations |
| HA unavailable/reconnect | disable HA/Wi-Fi and restore | Safe state, no crash, recover without flash |
| Cold boot/warm boot | USB log, photo/video | Восстановление |
| 24h soak | automated synthetic interactions, heap tracking | Нет роста ошибок или watchdog |
| Visual correctness | Scaled 480 ref + camera photo, RGB565 and glyph check | Review по design contract, не голая сумма пикселей |
| Development time | Время на layout и одно изменение alpha/icon/font | Отчёт о сопровождаемости и GUI limitations |

**Не ставить недоказанный FPS как гарантированный SLA.** После первого baseline измерения согласовать hard thresholds отдельно: важнее худшие p95/p99 и отсутствие видимых остановок. Привести реальные номера commit и конфигурацию clock/LVGL render buffering. Если native B отличается от A по clock/PSRAM policy, отдельно записать причину.

## 6. Сравнение качества preview и «один source»

| Эксперимент | Что должно работать | Что считать неуспехом |
|---|---|---|
| ESPBoards round-trip | YAML после import/export собирается, событие на лампе сохраняется | Потеря `!lambda`, substitutions, style или component |
| ESPHomeDesigner | LVGL export и mock HA values без смены архитектуры | Только display lambda / экспериментальный YAML ломается |
| ESPHome-LVGL-Simulator | Быстро показывает геометрию из **того же YAML** | Слишком много незаданных widgets, картинки/русские glyphs не показываются |
| LVGL Pro Editor | XML native preview + custom lamp widget → C | Невозможность воспроизвести в свободном edition из-за licensing |
| EEZ Studio | C export + mock events + compile | Flow runtime обязателен для нужной функции или C несовместим |
| SquareLine | Generated UI C + own callbacks separate | Codegen overwrites actions или license блокирует reproducibility |
| Native SDL | **Тот же ui_core**, что в ESP-IDF firmware, работает на Windows | Дублирование UI логики, расхождение LVGL versions |

Для браузерных preview **не вычислять pixel-diff к физической панели**: это разные rasterization engines. Для SDL native можно использовать screenshot regression, но аппаратная RGB565/цветовая коррекция всё равно отдельно.

## 7. Что считать решением

**ESPHome достаточно**, если native API и модульность перекрывают потребности, LA-01 alpha корректен, все элементы RH-01/кириллица работают без большой custom C++ прослойки, transition/touch response комфортны, reset/reconnect надёжны. Браузерный preview остаётся приблизительным, но компенсируется быстрым аппаратным тестированием.

**Нужен native**, если UI/animation потребуют глубоких custom draw и C widgets; ESPHome ломает композицию/opacity или требует объёмных нестабильных extensions; нужны реальные LVGL host screenshots из *одного UI core*; производительность ограничивает контроль PSRAM/DMA/LVGL scheduling; будущий P4 становится главным целевым устройством.

**Состояние решения:** открыто до завершения обоих S0–S5 и ключевых UI tests, [ADR-0003](../04-architecture/adr/0003-platform-evaluation.md). Не использовать взвешенную экспертную матрицу как замену measurements. Сохранять photos/logs с условиями, а результаты записывать в отдельный test report, а не редактировать первичные выводы.

## 8. Рекомендуемый формат отчёта после эксперимента

```text
test-run/
  manifest.md             board/photos, git SHA, versions, toolchain
  serial-boot.log
  metrics.csv              timestamp, frame_time, internal_heap, psram, events
  screenshots/             host and device separate
  assets-manifest.md       original/conversion, alpha, font glyphs
  esphome/                 build summary and failures
  native/                  build summary and failures
  conclusions.md           decision/risk/remaining unknowns
```

В файл отчёта обязательно поместить точное число failed frames/событий и способ его подсчёта; не называть синтетическую browser отрисовку real FPS.
