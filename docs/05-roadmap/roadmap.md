# Roadmap / план реализации

Этапы ориентированы на **гейты качества**, не на искусственные сроки. Не начинать массовую HA-интеграцию, пока не утверждён дизайн.

## Phase 0 — Repo / research baseline

- [x] Сформулировать миссию, требования, документацию и структуру.
- [x] Инвентаризировать заводской архив Guition (метаданные, без копирования assets).
- [x] Подготовить оригинальную SVG-композицию и pipeline 480/720 как подтверждение процесса.
- [ ] Создать удалённый GitHub репозиторий с нужными правами, залить локальную Git history.
- [ ] Присоединить полный файл внешнего Deep Research отчёта и каталог изображений с источниками.

**Gate:** релевантные данные не теряются, каждая ссылка имеет происхождение, проект можно клонировать и запустить renderer.

## Phase 1 — Visual direction / дизайн

- [ ] Выбрать 3 стилистически разные полноэкранные концепции 480×480: Ambient, Architectural, Modern Surface.
- [ ] Для каждой сделать room-home + bathroom-home + hallway-home.
- [ ] Для двух лучших — lighting + climate + timer screen.
- [ ] Оценить с реальной дистанции использования и при разной яркости.
- [ ] Принять palette/type/touch tokens, states и navigation; зафиксировать ADR.

**Gate:** выбранная цельная система, согласованы макеты на 480 и 720 без потери физической читаемости.

## Phase 2 — Hardware bring-up

- [ ] Снять точную модель и ревизию дисплея.
- [ ] Минимальный ESPHome `mipi_rgb` + GT911 + LVGL, touch/backlight/OTA.
- [ ] Benchmark RGB565, gradients, image assets, memory, display timing.
- [ ] Зафиксировать версии и аппаратные measurement baselines.

**Gate:** демонстрационный original ambient screen запускается на S3, и его отзывчивость приемлема.

## Phase 3 — UI-kit implementation

- [ ] Base frame, typography, icon pipeline, themes, page navigation.
- [ ] Clock, room comfort, weather, primary action, light/thermostat widgets.
- [ ] Towel timer, bathroom floor, ventilation, master lighting.
- [ ] Разные состояния: on/off/pending/unavailable/error.
- [ ] Desktop preview/test assets в CI и unit-тесты при каждом изменении.

**Gate:** всё работает на mock state без физического HA управления.

## Phase 4 — HA binding (1 panel)

- [ ] Реальные weather/temp/humidity sensors.
- [ ] Настроить ручной свет с учётом существующей автоматики.
- [ ] Lighting controls, climate entity, timer via HA.
- [ ] HA feedback and unavailable UX, safe test actions.

**Gate:** однокомнатная панель проходит hardware+functional acceptance.

## Phase 5 — Five-panel deployment

- [ ] Разделить profiles living/bedroom/office/bathroom/hallway.
- [ ] Утвердить единый look, отдельные screen layouts, backlight/day-night UX.
- [ ] Проверить пять одновременно подключённых экземпляров.
- [ ] Стабилизировать OTA, versioning, config template и документацию.

## Phase 6 — ESP32-P4 / 720×720 (отдельный трек)

- [ ] Выбрать конкретную 4″ 720×720 плату P4.
- [ ] Принести up display/touch/network, оценить ESPHome support.
- [ ] Протестировать source assets в 720 и найти их фактическую нагрузку.
- [ ] Сравнить визуальный результат с 480×480 при равной физической диагонали.
