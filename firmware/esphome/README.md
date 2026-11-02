# ESPHome · Guition 480×480 · RH-01

Входной файл — [`formapanel-rh01.yaml`](formapanel-rh01.yaml). Это первая
визуальная прошивка по [`references/01.jpg`](../../references/01.jpg): отдельный
растровый фон, настоящие LVGL labels для чисел и прозрачная сенсорная кнопка
светильника. Значения фиксированы для сравнения с образцом: `08:00`, `+2°`,
ветер `6`, `22°`, `45%`, `680 ppm`. Касание меняет только локальное изображение
светильника `on/off`; реальные светильники HA пока не подключены.

Цель схемы — **ESPHome 2026.10.1 / ESP-IDF**, сборка на HA либо в GitHub.
Для сборки на Windows не нужны Python, PlatformIO или ESP-IDF. Компиляция и аппаратная
проверка — разные этапы: успешный BIN ещё не подтверждает GPIO, ориентацию,
PSRAM и touch на конкретной ревизии платы.

Подробные [правила компоновки source](../../docs/04-architecture/source-composition.md)
и [сборка/preview с чистого checkout](../../docs/06-validation/build-and-preview-runbook.md)
описывают актуальное дерево и все пути. Общая [точка входа в разработку](../../docs/development.md).

```text
firmware/esphome/
  formapanel-rh01.yaml          # имя, demo-значения, packages
  boards/guition-s3-480.yaml   # ESP32-S3, LCD, GT911, подсветка
  packages/connection.yaml    # Wi-Fi, API, OTA
  packages/diagnostics.yaml   # heap, PSRAM, uptime, reset reason
  packages/rh01-ui.yaml       # шрифты, изображения, LVGL widgets
  secrets.yaml.example       # только названия ключей, без настоящих секретов
assets/generated/480x480/rh01-*.png
assets/source/fonts/Nunito-{Bold,Medium}.ttf
```

## Профили гостиной и спальни

Для браузерной рабочей среды список целей хранится в
[`config/workbench-targets.json`](../../config/workbench-targets.json).
Рабочая среда открывает и изменяет файлы самого репозитория; импорт или экспорт
в отдельный формат редактора не нужен.

| Цель | Прошивка | Настоящий LVGL preview |
|---|---|---|
| RH-01, исходный образец | [`formapanel-rh01.yaml`](formapanel-rh01.yaml) | [`previews/host-rh01.yaml`](previews/host-rh01.yaml) |
| Гостиная | [`targets/living.yaml`](targets/living.yaml) | [`previews/living.yaml`](previews/living.yaml) |
| Спальня | [`targets/bedroom.yaml`](targets/bedroom.yaml) | [`previews/bedroom.yaml`](previews/bedroom.yaml) |

Новые цели включают [`profiles/rh01-shared.yaml`](profiles/rh01-shared.yaml):
один исходник главной страницы, шрифтов и изображений, а также общую
[`packages/info-page.yaml`](packages/info-page.yaml). Гостиная сохраняет
исходные демонстрационные числа; спальня задаёт `23:10`, `21°`, `48%`,
`620 ppm` в своём [`profiles/bedroom.yaml`](profiles/bedroom.yaml).
Это примеры конфигурации, реальные HA-сущности не придуманы и не подключены.

На новых комнатных целях удержание лампы открывает общую страницу
«Информация», кнопка «Назад» возвращает домой. Обычное касание лампы сохраняет
локальное переключение её картинки. Исходная цель RH-01 не получает второй
страницы, событий или изменений оформления.

Изменение `packages/rh01-ui.yaml` отражается в обеих комнатных целях.
Изменение `packages/info-page.yaml` также применяется к обеим; смена чисел
одной комнаты выполняется в `profiles/living.yaml` или `profiles/bedroom.yaml`.
Когда потребуются разные главные страницы, профиль сможет выбрать другой
пакет главной страницы, сохранив общие ресурсы и дополнительные страницы.
Это пока одна общая сетка с разными данными, а не два разных дизайна.

`formapanel_asset_dir` задаёт каталог `assets` относительно основного YAML
или его абсолютный путь в рабочем сервере. Новые firmware-цели поддерживают
`formapanel_build_path`, previews — `preview_build_path`; рабочая среда может
переопределять их отдельным абсолютным каталогом на каждую цель.

Комнатные previews используют общий [`previews/room-backend.yaml`](previews/room-backend.yaml)
и сохраняют `rh01-on.bmp`, `rh01-off.bmp`, `info.bmp`. Каждый запуск требует
свежего каталога `ESPHOME_SNAPSHOT_DIR`. После трёх кадров появляется
`RH01_NATIVE_PREVIEW_COMPLETE`. Preview не подключается к HA и не управляет
нагрузками.

## Сборка через Home Assistant

В установленной среде используется [Studio Code Server + Workshop](../../docs/02-research/ha-browser-workflow.md):
оба приложения работают с одним checkout. Сохранить исходники, выбрать профиль
в Workshop и запустить нужную операцию. Следующие шаги относятся только к
первичной настройке отдельного входа в существующем Device Builder.

1. Скопировать дерево `firmware/` и `assets/` в выделенную папку
   `/config/esphome/formapanel-rh01/`. Сохранить вложенную структуру.
2. В Device Builder создать `/config/esphome/formapanel-rh01.yaml`:

   ```yaml
   substitutions:
     formapanel_asset_dir: formapanel-rh01/assets

   packages:
     panel: !include formapanel-rh01/firmware/esphome/formapanel-rh01.yaml
   ```

3. В локальный `firmware/esphome/packages/secrets.yaml` внутри checkout добавить ключи
   `wifi_ssid`, `wifi_password`, `formapanel_api_key`,
   `formapanel_ota_password`. Если Wi-Fi ключи уже есть, использовать их.
   API key — сгенерированный Device Builder ключ, 32 байта в Base64.
   Сохранить файл с правами `0600`; он игнорируется Git. Не заменять общий
   `/config/esphome/secrets.yaml`: существующие Wi-Fi значения можно взять
   оттуда, но секреты этого package должны быть доступны рядом с ним.
4. Выполнить **Validate**, затем **Install → Manual Download**. Первая
   компиляция ESP-IDF загружает инструменты на HA-сервер и может занять время.
5. Для первого USB запуска скачать **Factory image**, для последующего
   обновления — OTA image. Не устанавливать BIN до проверки аппаратного
   профиля и recovery-плана по [S0](../../docs/05-roadmap/phase-s0-ha-local-build-guition.md).

При прямой сборке исходного RH-01 его default — `formapanel_asset_dir: ../../assets`.
У `targets/*.yaml` и `previews/*.yaml` default — `../../../assets`.
Workshop задаёт абсолютный asset root. Пути ресурсов ESPHome считает
относительно основного device YAML, поэтому HA-wrapper переопределяет этот
параметр. Шрифты и картинки локальные, обращения к Google Fonts во время
сборки нет.

## Что проверить на панели

- Сверить PCB/ревизию, 16 MB flash и 8 MB octal PSRAM с фактическим устройством.
- Проверить все края изображения, цвета и ориентацию; здесь используется
  стандартная ориентация preset, без непроверенных поворотов.
- Нажать лампу в нижнем правом углу: свечение должно переключаться, в логах
  появится `RH-01 demo lamp toggled (local UI only)`.
- Из HA проверить `Display Backlight`, память/PSRAM и OTA. Это служебные
  сущности панели; бытовые нагрузки конфиг не затрагивает.

Невидимая область лампы — `112×128 px`; её видимое изображение — `96×112 px`.
Clock/температура/климат остаются живыми слоями, поэтому будущие HA-сенсоры
можно подключить без запекания данных в фон. Автоматическая смена времени
пока выключена, чтобы экран был воспроизводим при визуальной проверке.

## Проверенные источники схемы

Схема сверена с официальной документацией и исходниками тега 2026.10.1:

- [MIPI RGB](https://esphome.io/components/display/mipi_rgb/),
  [Guition preset](https://github.com/esphome/esphome/blob/2026.10.1/esphome/components/mipi_rgb/models/guition.py).
- [Guition pin profile](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/):
  SPI `CLK48/MOSI47`, I²C `SDA19/SCL45`, подсветка `GPIO38`.
  SPI нужен для инициализации ST7701S дополнительно к RGB preset; он задан
  в текущем board-пакете и диагностическом YAML S0.
- [LVGL](https://esphome.io/components/lvgl/),
  [widgets](https://esphome.io/components/lvgl/widgets/),
  [RGB565 и alpha channel](https://esphome.io/components/image/),
  [GT911](https://esphome.io/components/touchscreen/gt911/).

Точный результат HA Validate/Compile, версии и артефакты фиксируются в отчёте
текущей сборки. Аппаратный bring-up и реальные HA-данные остаются следующими
проверками.
