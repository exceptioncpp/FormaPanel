# Карта документации

**Статус текстов:** `fact` — подтверждено архивом/официальной документацией; `target` — требование; `proposal` — предлагаемое решение; `open` — требует исследования/замера. Не смешивать статусы.

- [00 — Vision](00-vision/product-vision.md) — позиционирование, границы, принципы.
- [01 — Требования](01-requirements/requirements.md), [пять комнат](01-requirements/rooms.md), [критерии приёмки](01-requirements/acceptance.md).
- [02 — Исследование](02-research/references.md), [сравнение кандидатов](02-research/candidates.md), [заводская Guition](02-research/guition-factory-demo.md), [открытые вопросы](02-research/open-questions.md).
- **[Исследование баз прошивки, октябрь 2026](02-research/firmware-platforms-2026-10.md)** — ESPHome/LVGL 9, ESP-IDF/LVGL, Arduino, готовые проекты, ресурсные риски и взвешенный выбор.
- **[Средства визуального редактирования и preview](02-research/lvgl-visual-tools-2026-10.md)** — ESPBoards, ESPHomeDesigner, ESPHome-LVGL-Simulator, LVGL Pro, EEZ, SquareLine и настоящий LVGL SDL.
- [Windows 11 build/preview и план CI](02-research/build-preview-workflows.md) · [реестр источников](02-research/research-source-register-2026-10.md).
- [ADR-0003 — критерии выбора](04-architecture/adr/0003-platform-evaluation.md) · [RH-01/LA-01 A/B протокол](06-validation/rh01-platform-ab-test.md).
- **[RH-01 — утверждённая компоновка главной жилой панели](03-design/room-home-reference-RH-01.md)** — точное описание UI 480×480, мотивы выбора/отказа, список открытых вариантов света и шрифта.
- **[LA-01 — утверждённая иконка света](03-design/light-action-reference-LA-01.md)** — тонкий полукруглый подвесной плафон, полупрозрачный свет, градиентно затухающий провод, состояния on/off.
- **[Структура референсов и ассетов](03-design/asset-library.md)** — отдельное хранение проверенных UI-макетов, hi-res фонов, исходников виджетов и сгенерированных ресурсов 480/720.
- [03 — Дизайн](03-design/design-system.md), [экраны и навигация](03-design/screens.md), [480/720 pipeline](03-design/resolution-strategy.md), [визуальное ревью](03-design/visual-review.md).
- [04 — Архитектура](04-architecture/architecture.md), [контракт HA](04-architecture/ha-contract.md), [профили железа](04-architecture/hardware.md), [ADR-0001](04-architecture/adr/0001-native-lvgl.md), [ADR-0002](04-architecture/adr/0002-source-resolution-independence.md).
- **[S0 — сборка ESPHome локально в HA и тесты Guition](05-roadmap/phase-s0-ha-local-build-guition.md)** — детальная пошаговая инструкция: подготовка и backup, Device Builder, полный диагностический YAML, USB, OTA, Git Packages, протокол приёмки.
- [05 — План](05-roadmap/roadmap.md), [backlog](05-roadmap/backlog.md).
- [06 — Проверка](06-validation/test-plan.md), [метрики](06-validation/performance.md).
- [07 — Правовые вопросы](07-legal/licensing.md).

## Как поддерживать актуальность

1. Каждое требование имеет ID (`FR`, `UX`, `NFR`, `HW`) и привязано к тесту.
2. Дизайнерский выбор фиксируется в ADR с сравнением альтернатив, а не стирает их.
3. Для каждой внешней ссылки сохранять дату проверки и отличать реальные ESP32/LVGL кадры от HTML/концептов.
4. Для каждого аппаратного профиля указывать реальные данные: модель, ревизия, touch IC, flash/PSRAM, controller, сборка ESPHome.
5. После первого прототипа добавлять фотографии реального экрана и замеры, не заменяя ими макеты.
