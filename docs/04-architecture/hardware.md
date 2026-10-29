# Hardware profiles

## `guition-s3-480` — текущая платформа

- Пользователь: 4.0 inch ESP32-S3 480×480 IPS, capacitive touch, без собственных реле; фактическая маркировка и ревизия **не предоставлены**.
- Вероятное семейство: Guition/ESP32-S3-4848S040, ST7701S, GT911, PSRAM. Confirm exact board before flashing.
- Официальная конфигурация ESPHome: `display.platform: mipi_rgb`, `model: GUITION-4848S040` (https://esphome.io/components/display/mipi_rgb/).
- Официальная LVGL component ориентирована на LVGL 9 (https://esphome.io/components/lvgl/).
- Вопросы: pin mapping, backlight GPIO, размер и режим PSRAM, display timing, orientation, touch offsets.
- Известные исторические issues для ESPHome 2026.7.1: https://github.com/esphome/esphome/issues/17784 (rotation), https://github.com/esphome/esphome/issues/17810 (timings). Проверить их текущий статус, не применять старые workarounds автоматически.

## `esp32-p4-720` — экспериментальная перспектива

- 4″, 720×720, ESP32-P4; модель платы **ещё не выбрана**, её схема/wifi/rgb/DSI/touch не верифицированы.
- Возможный референс: Waveshare ESP32-P4-86-Panel-ETH-2RO, 720×720, помечен experimental в Tessera в октябре 2026; требуется отдельная аппаратная проверка.
- P4 — не pin-compatible и не обязательно network-compatible с S3: учитывать модуль/сопроцессор для Wi-Fi и иные контроллеры дисплея.

## Smoke test hardware

1. Сохранить фото обеих сторон платы и её полное обозначение.
2. Считать boot log и flash/PSRAM info, проверить питание и яркость.
3. LVGL test screen RGB stripes, градиент, текст, touch grid, reset, OTA.
4. Проверить соответствие координат touch после ориентации.
5. Проверить режимы sleep/bright/night, warm/cold reboot, restart HA.
6. Снять измерения реального FPS/heap/PSRAM/потребления по экрану.
