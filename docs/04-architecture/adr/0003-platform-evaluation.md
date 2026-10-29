# ADR-0003 — Стратегия выбора firmware/UI toolchain для FormaPanel

- **Статус:** **Proposed / evaluation gate**, НЕ принят окончательный firmware stack
- **Дата:** 2026-10-29
- **Связь с ADR-0001:** [ADR-0001](0001-native-lvgl.md) остаётся действующим **provisional** baseline для ESPHome. Этот ADR уточняет проверку альтернатив и не отменяет ADR-0001.
- **Контекст:** [платформы](../../02-research/firmware-platforms-2026-10.md), [визуализация](../../02-research/lvgl-visual-tools-2026-10.md), [build/CI](../../02-research/build-preview-workflows.md), [A/B протокол](../../06-validation/rh01-platform-ab-test.md).

## Контекст

FormaPanel должна управлять локальными Home Assistant entities с 5 физических интерьерных панелей Guition ESP32-S3-4848S040. Проект требует пользовательской 480×480 художественной графики, точной кириллической типографики, отдельного RGBA overlay светильника [LA-01](../../03-design/light-action-reference-LA-01.md), переходов и выразительных custom LVGL widgets. Перспективная ESP32-P4 720×720 плата пока не выбрана.

У ESPHome + LVGL 9 есть сильные преимущества: официальный профиль Guition, нативная HA API, OTA и YAML packages. У native ESP-IDF + LVGL 9 — полный C API, контроль graphics/PSRAM и достоверный shared LVGL SDL host preview. В то же время native требует отдельной инфраструктуры HA, а ESPHome browser preview (ESPBoards/ESPHome-LVGL-Simulator) не выполняет настоящий LVGL C renderer.

**Основной риск выбора на бумаге:** либо преждевременно запереть художественную UI-систему в ограничениях ESPHome YAML, либо преждевременно написать сложный C/networking stack там, где ESPHome полностью закрывает UX.

## Предлагаемое решение

1. **Не менять production baseline**: ESPHome + LVGL 9 + ESP-IDF для первого Guition smoke test, сохраняя provisional статус.
2. **Реально выполнить два коротких PoC** на **одном** экранном контракте RH-01/LA-01 и одинаковых asset masters: A = ESPHome, B = native ESP-IDF.
3. На ESPHome lane испытать ESPBoards LVGL Designer, ESPHomeDesigner, ESPHome-LVGL-Simulator. На native lane испытать LVGL Pro Editor, EEZ Studio (без обязательного Flow), SquareLine и официальный LVGL PC SDL simulator.
4. **Сравнивать одно и то же на физическом 480×480**: внешний вид/alpha, custom widget, fonts, touch, transitions, full/partial redraw, heap, PSRAM, flash, Wi-Fi/HA reconnect, цена изменения UI. Browser emulator screenshots не являются эталоном.
5. По результатам заполнить decision table и перевести **одну** платформу в Accepted; вторую оставить как reference/benchmark или отложить. Не принимать другую платформу из-за только одного красивого static screenshot.

## Критерии перехода в Accepted

- Подтверждена аппаратная ревизия и восстановление firmware (factory backup/rollback).
- Smoke test display/GT911/backlight/OTA работает без незафиксированных vendor patches.
- RH-01 и LA-01 реализованы в полном соответствии с approved дизайн-контрактом.
- На реальном Guition просмотрены contrast/alpha/glow/кириллица/RGB565 и измерена отзывчивость touch.
- Показаны p50/p95/p99 frame times, internal RAM/PSRAM и flash. Не приравнивать одно число FPS к стабильности.
- Подтверждён корректный HA state contract (off/on/pending/unavailable) и reconnect.
- Доказана повторяемая локальная сборка Windows 11 и GitHub CI (после появления рабочих skeletons).
- Отдельно оценена стоимость сопровождения UI для 5 комнат и будущего P4.
- Нет критичных blockers по лицензии ассетов/визуального editor.

## Предлагаемые результаты, но НЕ уже выполненные

- `docs/06-validation/rh01-platform-ab-test.md` — протокол.
- `firmware/esphome` и `firmware/native` — **будущие** короткие compileable skeletons, не добавляются в текущем docs-only PR.
- `tools/preview/lvgl-pc` — **будущий** SDL host harness.
- `.github/workflows/firmware.yml` — **будущая** CI работа, не добавляется, пока хотя бы один реальный build не собирается.
- Реальные логи, изображения дисплея и измерения — будущий отдельный test report.

## Что не принимается сейчас

- Нельзя объявить ESPHome достаточным или native необходимым по рекламным роликам.
- Нельзя назвать browser ESPHome simulator pixel-perfect, пока это JS интерпретация YAML.
- Нельзя использовать paid LVGL Pro CLI в обязательном GitHub Actions workflow без права лицензии.
- Нельзя обещать портабельность на неопределённую ESP32-P4 плату.
- Нельзя менять approved [RH-01](../../03-design/room-home-reference-RH-01.md)/[LA-01](../../03-design/light-action-reference-LA-01.md) ради удобства конкретного GUI editor.

## Последствия и компромиссы

**Положительные:** решение основано на сравнимых измерениях, меньше риск переписывания UI; исходные ассеты и mock states общие; Git хранит source-of-truth; editor не становится обязательной cloud зависимостью.

**Отрицательные:** на этапе исследования придётся дважды реализовать минимальную RH-01 scene; простая ESPHome lane может получить меньшую достоверность desktop preview; native lane требует дополнительного hardware + HA glue.

**Пересмотр:** после PoC с логами и screenshots, а затем при появлении конкретной ESP32-P4 720 платы.
