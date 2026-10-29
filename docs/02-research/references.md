# Исследования: индекс источников

**Дата контрольной сверки:** 2026-10-29. Ссылки — отправные точки для проверки; скриншот без исходников не является готовой темой. Конкретные версии, лицензии и активность требуется фиксировать отдельно перед заимствованием кода.

## Нативный LVGL / Guition / ESPHome

- Официальный ESPHome LVGL (LVGL 9): https://esphome.io/components/lvgl/
- Официальный MIPI RGB с моделью `GUITION-4848S040`: https://esphome.io/components/display/mipi_rgb/
- Профиль устройства: https://devices.esphome.io/devices/Guition-ESP32-S3-4848S040
- Guition home assistant community, длинная ветка: https://community.home-assistant.io/t/guition-4-480x480-esp32-s3-4848s040-smart-display-with-lvgl/729271
- [Alaltitov](https://github.com/alaltitov/Guition-ESP32-S3-4848S040) — проект экранов, русская локаль, rich widgets.
- [PrayerfulDrop](https://github.com/PrayerfulDrop/ESPHome-Guition-ESP32-S3-4848S040) — шесть тем и готовые страницы.
- [EspControl](https://jtenniswood.github.io/espcontrol/screens/4848s040) — готовый UI/процессы для 4″ 480×480, поддержка разных карточек.
- [Tessera](https://github.com/MaxGramser/homeassistant_espscreen) — native LVGL, multi-panel менеджер, локальное управление; визуальный редактор, другая архитектура.
- [ESPHome LVGL пример](https://github.com/jtenniswood/esphome-lvgl/tree/main/guition-esp32-s3-4848s040) — структурирование theme, device, assets.
- [VahaC](https://github.com/VahaC/ESP32-4848S040-EspHome-LVGL) — ещё один пример HA-dashboard под целевой экран.
- [ESPHome modular buttons](https://github.com/agillis/esphome-modular-lvgl-buttons) — переиспользуемые controls; подробную совместимость проверить.
- [ESPHome UI kit](https://github.com/mplogas/esphome-ui-kit) — паттерны модульного UI, проверить состояние.

## Профессиональные инструменты и дизайн-процесс

- LVGL: https://lvgl.io/
- LVGL Forum: https://forum.lvgl.io/
- EEZ Studio: https://github.com/eez-open/studio
- SquareLine Studio: https://squareline.io/
- ESPBoards LVGL designer: https://lvgl.espboards.dev/
- OpenHASP: https://www.openhasp.com/ — MQTT/LVGL проект, отдельный runtime.

## Визуальное сообщество (источники для ручной кураторской оценки)

- Home Assistant Community: https://community.home-assistant.io/
- Reddit Home Assistant: https://www.reddit.com/r/homeassistant/
- Reddit ESP32: https://www.reddit.com/r/esp32/
- Reddit embedded: https://www.reddit.com/r/embedded/
- Pinterest: https://www.pinterest.com/ — использовать только как вторичный индекс иллюстраций; проверять автора и исходник.
- Behance: https://www.behance.net/ ; Dribbble: https://dribbble.com/ — концепты, не доказательство работы на MCU.

## Достоверность

- **A**: исходный архив/официальные docs и/или проверенная прошивка на железе.
- **B**: публичный репозиторий с явной моделью, фото и инструкциями.
- **C**: скриншот, рендер, пост или маркетинговый материал без воспроизводимой прошивки.

**Важно:** глубокий исследовательский отчёт из отдельного интерфейса Deep Research не приложен сюда как доступный файл; документ пока фиксирует **проверяемые первоисточники и выводы, присутствующие в рабочем контексте**, а не притворяется дословной копией отчёта. Когда отчёт появится как файл, включить его в `docs/02-research/raw/` вместе с датой и ссылками.
