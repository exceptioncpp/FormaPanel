# Карта документации

**Статус текстов:** `fact` — подтверждено архивом/официальной документацией; `target` — требование; `proposal` — предлагаемое решение; `open` — требует исследования/замера. Не смешивать статусы.

- [00 — Vision](00-vision/product-vision.md) — позиционирование, границы, принципы.
- [01 — Требования](01-requirements/requirements.md), [пять комнат](01-requirements/rooms.md), [критерии приёмки](01-requirements/acceptance.md).
- [02 — Исследование](02-research/references.md), [сравнение кандидатов](02-research/candidates.md), [заводская Guition](02-research/guition-factory-demo.md), [открытые вопросы](02-research/open-questions.md).
- [03 — Дизайн](03-design/design-system.md), [экраны и навигация](03-design/screens.md), [480/720 pipeline](03-design/resolution-strategy.md), [визуальное ревью](03-design/visual-review.md).
- [04 — Архитектура](04-architecture/architecture.md), [контракт HA](04-architecture/ha-contract.md), [профили железа](04-architecture/hardware.md), [ADR-0001](04-architecture/adr/0001-native-lvgl.md), [ADR-0002](04-architecture/adr/0002-source-resolution-independence.md).
- [05 — План](05-roadmap/roadmap.md), [backlog](05-roadmap/backlog.md).
- [06 — Проверка](06-validation/test-plan.md), [метрики](06-validation/performance.md).
- [07 — Правовые вопросы](07-legal/licensing.md).

## Как поддерживать актуальность

1. Каждое требование имеет ID (`FR`, `UX`, `NFR`, `HW`) и привязано к тесту.
2. Дизайнерский выбор фиксируется в ADR с сравнением альтернатив, а не стирает их.
3. Для каждой внешней ссылки сохранять дату проверки и отличать реальные ESP32/LVGL кадры от HTML/концептов.
4. Для каждого аппаратного профиля указывать реальные данные: модель, ревизия, touch IC, flash/PSRAM, controller, сборка ESPHome.
5. После первого прототипа добавлять фотографии реального экрана и замеры, не заменяя ими макеты.
