# Архитектура FormaPanel

Актуальное состояние: **01.11.2026**. Основа — ESPHome **2026.10.1**,
LVGL **9.5.0**, ESP-IDF **5.5.6** в проверенном HA build image.
Workshop **0.1.1** предоставляет сборку и настоящий host/snapshot preview.
Подробная [компоновка исходников](source-composition.md),
[сборка и предпросмотр](../06-validation/build-and-preview-runbook.md),
[процесс разработки](../02-research/effective-ui-development-2026-11.md).

## Data / control flow

```text
   HA VM on local Proxmox (states + services + scenes + climate)
                   ⇅ ESPHome native API
    FormaPanel ESP32-S3 (Wi-Fi, ESPHome, LVGL9, GT911)
          ↳ state adapter → UI widgets → screen
          ↳ touch event → HA action → state confirmation
```

Это целевой поток данных. В текущей прошивке настроены сеть, API, OTA и
служебные сущности, но UI ещё использует demo substitutions: реальные
подписки на домашние датчики и команды бытовым нагрузкам не подключены.
Действующая лампа переключает только локальную картинку.
В целевой схеме исполнительные функции и автоматика остаются на стороне HA.

## Распределение слоёв

| Слой | Роль | Статус |
|---|---|---|
| `hardware/` | материалы о ревизии платы и аппаратных измерениях | визуальный прототип испытан владельцем; подробные измерения не приложены |
| `firmware/esphome/boards/` | GPIO, дисплей, touchscreen, backlight, PSRAM | Guition preset настроен, config/compile проверены |
| `firmware/esphome/packages/` | общая графика, widgets, info, connection и diagnostics | реализованы RH-01 и общий info-экран |
| `firmware/esphome/profiles/` | комнатные параметры и выбор общих пакетов | living и bedroom на общей композиции |
| `firmware/esphome/targets/` | входы для физических устройств | две комнатные цели; отдельный базовый RH-01 в корне |
| `firmware/esphome/previews/` | host/snapshot entry и сценарии кадров | реальный LVGL; RH-01 on/off, комнаты on/off/info |
| `ui/tokens/` | palette, type scale, spacing, state colors | стартовые токены |
| `ui/mockups/` | дизайн-композиции без runtime логики | один пример |
| `assets/source/` | master-фоны, графика, Nunito с OFL и metadata | используются RH-01 renderer и локальные TTF |
| `config/ha/` | имена entity, profile binding, действия | примеры без credentials |
| `tools/ha-workbench/` | HA Ingress, validate/build/native preview | установлена версия 0.1.1 |
| `tests/` | статические/asset/server regression checks | 11 тестов проходят; аппаратные проверки отдельно |

По [отзыву владельца 01.11](../06-validation/rh01-hardware-feedback-2026-11-01.md)
прототип успешно испытан на панели и выглядит отлично. Следующий шаг —
[HA bindings и навигация](../05-roadmap/ha-functional-ui-plan.md), после согласования экранов.

## Среда разработки

Studio Code Server и Workshop используют один Git checkout в HA:
`/config/esphome/formapanel-rh01` для IDE и тот же каталог через read-only
mount `/homeassistant/esphome/formapanel-rh01` для worker. ESPHome раскрывает
настоящие packages/includes; перенос всей прошивки между приложениями не нужен.
Стабильные служебные wrappers и metadata находятся в приватном `/data`
Workshop; они не являются редактируемыми исходниками UI.

Обычная итерация — Save в IDE, кнопка native preview, затем просмотр PNG.
Автосборка после Save, интерактивный SDL/noVNC и универсальный визуальный
редактор репозитория не внедрены. Предложенные layout/behavior/mock/HA
слои описаны в методологии; соответствующее дерево ещё не создано.

## Выбор ESPHome + LVGL

Зафиксирован как **начальный technical baseline**. Спорный вопрос: будет ли дизайнерская графика и анимация достигать нужного качества/производительности при YAML-сборке; до подтверждения профайлингом не объявлять ESP-IDF ненужным навсегда. Подробнее ADR-0001.

## Принципы интерфейса с HA

- Есть только источник истинного состояния — HA. Оптимистичный визуальный отзыв не подменяет подтверждённое состояние.
- Не полагаться на `entity_id`, встроенные в общий компонент: bindings задаются комнатным профилем.
- Разделять визуализацию `unavailable`, отсутствие обновления, timeout команды и реальное выключение.
- Свой weather API, QWeather или ip-geolocation не используются.
- При недоступности HA активный UI должен показывать проблему, **не обещать offline управление**.

## Версионирование

- UI, assets, source и документация хранятся вместе; изменения сначала проверяются на mock/native, затем на панели.
- Точные версии build stack закреплены в HA образе и отчётах; `esphome.min_version` в YAML — нижняя граница, а не pin toolchain.
- Firmware и assets должны собираться из одного commit с хранением build manifest.
- Пока текущие изменения не закоммичены, сохранять working tree и private secrets отдельно. Наличие Git remote не означает выполненный push или backup.
