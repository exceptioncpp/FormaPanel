# Roadmap / план реализации

Этапы ориентированы на **гейты качества**, не на искусственные сроки. Не начинать массовую HA-интеграцию, пока не утверждён дизайн.

**Реализация 29.10.2026:** добавлен [основной RH-01 экран](../03-design/rh01-implementation.md) по `references/01.jpg` и ESPHome конфигурация для сборки на HA. Экран пока на mock-данных; это не закрывает аппаратные гейты S0. Фактический статус Validate/Compile — в [отчёте](../06-validation/rh01-build-2026-10-29.md).

**Среда разработки 31.10.2026:** установлена [FormaPanel Workshop в HA](../02-research/ha-browser-workflow.md). Studio Code Server редактирует общий Git checkout; из него собираются настоящий LVGL preview и ESP32 BIN. Проверены RH-01, демо гостиной/спальни и общая дополнительная страница. [Протокол проверки](../06-validation/ha-workshop-2026-10-31.md). Полный внешний отчёт сохранён [с разбором](../02-research/external/README.md). Аппаратные испытания и реальные HA bindings остаются следующим этапом.

**Среда 01.11.2026:** Workshop 0.1.1 сохраняет incremental cache;
[реальное layout-изменение заняло 7.88 с](../06-validation/ha-workshop-incremental-2026-11-01.md).
Точки входа: [процесс разработки](../development.md),
[компоновка source](../04-architecture/source-composition.md),
[сборка/preview](../06-validation/build-and-preview-runbook.md).

**Новый факт 01.11.2026:** владелец успешно испытал прототип на железе и
подтвердил отличный внешний вид. [Зафиксированный отзыв](../06-validation/rh01-hardware-feedback-2026-11-01.md).
**Следующая задача — [HA-функциональность и интерактивная навигация](ha-functional-ui-plan.md)**;
сначала согласовать предложенные экраны и жесты. Подробные S0 измерения и
OTA/reconnect протоколы не считаются выполненными автоматически из визуального
отзыва; [аппаратный план](phase-s0-ha-local-build-guition.md) сохраняется.
Действующий GitHub workflow пока проверяет assets/Python.

## Phase 0 — Repo / research baseline

- [x] Сформулировать миссию, требования, документацию и структуру.
- [x] Инвентаризировать заводской архив Guition (метаданные, без копирования assets).
- [x] Подготовить оригинальную SVG-композицию и pipeline 480/720 как подтверждение процесса.
- [x] Настроить Git origin и общий checkout с историей в HA.
- [ ] Проверить/закоммитить и отправить текущие изменения через GitHub auth владельца; remote не заменяет backup рабочего дерева.
- [x] Сохранить полный [внешний Deep Research отчёт](../02-research/external/README.md) с происхождением и разбором.
- [ ] Завершить каталог изображений с источниками и условиями использования.

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
