# ADR-0001 — Native LVGL for primary implementation

- **Status:** Provisional / proposed
- **Date:** 2026-10-29

## Context

Нужны пять высококачественных 4″ панелей ESP32-S3, работающих с локальным HA. Web UI Home Assistant не исполняется нативно на ESP32-S3, а RemoteWebView требует внешнего server-renderer.

## Decision

Начать с **ESPHome + LVGL 9** с общими компонентами и параметрами комнат. Нативный renderer и минимальные внешние runtime зависимости — предпочтение. Держать ESP-IDF/native LVGL как fallback для эффектов или performance; не вводить его в initial MVP без измерений.

## Alternatives

- ESP-IDF + LVGL: больше контроля, больше низкоуровневого кода и инструментов.
- RemoteWebView: гибкая HTML/CSS визуализация, но runtime-зависимость от локального Chromium-сервера и передачи фреймов; не текущий baseline.
- Tessera/EspControl: готовые решения, визуально и архитектурно не совсем совпадают с целевой дизайн-системой. Используются как reference.

## Review gate

Визуальный прототип Ambient + Lighting + Climate должен поместиться в ресурсах реального ESP32-S3 без неприемлемой задержки/артефактов. Иначе повторное решение ADR.
