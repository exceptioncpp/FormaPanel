# Архитектура v0.1

## Data / control flow

```text
   HA VM on local Proxmox (states + services + scenes + climate)
                   ⇅ ESPHome native API
    FormaPanel ESP32-S3 (Wi-Fi, ESPHome, LVGL9, GT911)
          ↳ state adapter → UI widgets → screen
          ↳ touch event → HA action → state confirmation
```

На стороне Home Assistant живут автоматизация света, контроль тёплого пола, вентиляции и полотенцесушителей, погодные сущности и агрегаты; панель **не является исполнительным узлом**.

## Распределение слоёв

| Слой | Роль | Статус |
|---|---|---|
| `hardware/` | pinout, LVGL display, touchscreen, brightness, PSRAM | проектируется |
| `firmware/esphome/` | сборка ESPHome, пакеты, события, HA subscriptions | не реализован |
| `ui/tokens/` | palette, type scale, spacing, state colors | стартовые токены |
| `ui/mockups/` | дизайн-композиции без runtime логики | один пример |
| `assets/source/` | разрешение-независимая графика | оригинальная абстракция |
| `config/ha/` | имена entity, profile binding, действия | примеры без credentials |
| `tests/` | статические/рендер проверки, затем hardware smoke tests | bootstrap |

## Выбор ESPHome + LVGL

Зафиксирован как **начальный technical baseline**. Спорный вопрос: будет ли дизайнерская графика и анимация достигать нужного качества/производительности при YAML-сборке; до подтверждения профайлингом не объявлять ESP-IDF ненужным навсегда. Подробнее ADR-0001.

## Принципы интерфейса с HA

- Есть только источник истинного состояния — HA. Оптимистичный визуальный отзыв не подменяет подтверждённое состояние.
- Не полагаться на `entity_id`, встроенные в общий компонент: bindings задаются комнатным профилем.
- Разделять визуализацию `unavailable`, отсутствие обновления, timeout команды и реальное выключение.
- Свой weather API, QWeather или ip-geolocation не используются.
- При недоступности HA активный UI должен показывать проблему, **не обещать offline управление**.

## Версионирование

- `docs/` и `ui/` проектируются раньше рабочего firmware.
- Конкретные ESPHome release, LVGL release, TFT/touch revision и их патчи закрепляются в документе о сборке при hardware bring-up.
- Firmware и assets должны собираться из одного commit с хранением build manifest.
