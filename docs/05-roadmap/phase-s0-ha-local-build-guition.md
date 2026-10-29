# FormaPanel — S0: локальная сборка ESPHome на Home Assistant и первый запуск Guition

> **Статус:** инструкция для выполнения; приведённый YAML — **непроверенный на железе** стартовый шаблон, не уже собранная прошивка.  
> **Актуальность:** 29.10.2026. **Порядок работ:** Home Assistant Device Builder → USB-прошивка → испытания на экране → OTA → GitHub Remote Packages → **только затем GitHub Actions**.  
> **Устройство:** Guition ESP32-S3-4848S040, 4″ RGB IPS 480×480, ST7701S, GT911; точная ревизия **не подтверждена**.  
> **Цель:** пройти S0 на реальной панели, без установки Python, ESP-IDF, CMake, Ninja или PlatformIO на Windows.

## 1. Что должно получиться

Критерий готовности S0: **локальная компиляция в HA** завершается успешно, дисплей отображает тестовую LVGL-страницу, сенсорные касания регистрируются и нажимают кнопку, подсветка регулируется, устройство подключается к Wi-Fi и HA API, доступны показатели памяти/PSRAM, выполняется OTA-обновление. Затем тот же протестированный код переносится в GitHub, подключается в HA как Remote Package и вновь успешно собирается.

Это **не** разработка полноценного RH-01/LA-01. В S0 отсутствуют художественные фоны, русские шрифты, анимации, управление настоящими светильниками и климатом. Они начинаются с S1. Native ESP-IDF и CI также остаются за пределами S0.

```text
                 GitHub: FormaPanel
          проверенные общие YAML-пакеты
             (необязательно для первого старта)
                         │
                         ▼
          Home Assistant ESPHome Device Builder
             Validate → Compile → .bin
               local secrets.yaml
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
      первый USB                   дальнейшие OTA
   (ESPHome Web)                     через LAN
          └──────────────┬──────────────┘
                         ▼
             Guition ESP32-S3 480×480
```

Windows используется только как терминал браузера Chrome/Edge для USB и как место временного хранения BIN. **Возможен USB-UART-драйвер конкретной ревизии**, это не установка полноценного SDK.

### Контроль версии

Сверить версию ESPHome непосредственно в HA Device Builder и записать в отчёт. **ESPHome 2026.10.1 вышел 27.10.2026**: [upstream release](https://github.com/esphome/esphome/releases/tag/2026.10.1), [PyPI](https://pypi.org/project/esphome/2026.10.1/). В раннем исследовании проекта приводится 2026.10.0; на S0 используем **фактически установленную стабильную версию** и не меняем её в середине сравнения. Не переносить YAML с beta/master без повторной валидации.

## 2. Этап S0-0: физическая подготовка, ревизия и backup

**Не начинать запись во flash до проверки пункта о восстановлении прежней прошивки.**

- [ ] Сделать фотографии обеих сторон платы, надписи PCB/ревизии, чипа USB-UART, LCD/touch маркировки; зафиксировать исходную ориентацию экрана и USB.
- [ ] Определить установленную прошивку и найти установочный образ/инструкцию возвращения **для точной ревизии**. Если исходная прошивка важна — получить backup или проверенный установочный образ *до записи ESPHome*. ESPHome Web **не является инструментом полного backup**. При необходимости использовать временный esptool на отдельной машине/сервере; не устанавливать SDK на основной Windows-ПК.
- [ ] Проверить DATA USB-C кабель, устойчивое питание и наличие последовательного порта в системе. Если порт отсутствует, проверить USB-UART драйвер (не предполагать заранее CH340).
- [ ] Определить documented вход в bootloader (BOOT/RESET) по плате. **Не замыкать случайные GPIO** и не выполнять массовое erase-flash при неудаче.
- [ ] Убедиться, что домашний Wi-Fi имеет 2,4 ГГц SSID и HA видит устройства в этой сети (не блокируются ESPHome API/OTA, mDNS либо доступ по IP).
- [ ] Зафиксировать, что наша модель панели **не управляет реле**. В community-примере Guition встречаются GPIO реле, но они не нужны и **не должны включаться** в S0.

| Компонент | Типовой Guition профиль | Основание / риск |
|---|---|---|
| MCU | ESP32-S3 | [ESPHome Devices](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/) |
| Flash / PSRAM | 16 MB / 8 MB octal 80MHz | Типовая конфигурация; **подтвердить** по логам/плате |
| LCD | ST7701S RGB 480×480 | [MIPI RGB](https://esphome.io/components/display/mipi_rgb/) имеет preset `GUITION-4848S040` |
| Touch | GT911, SDA GPIO19, SCL GPIO45 | community-пины; **проверить на физическом экземпляре** |
| Backlight | LEDC GPIO38, 150Hz | community-пин, проверить |
| Framework | ESP-IDF через ESPHome | Официальный поддерживаемый стек |

**Gate:** есть план безопасного USB recovery и фактическая информация о железе. Если исходную firmware восстановить необходимо, а recovery/backup отсутствует — остановиться.

## 3. Этап S0-1: подготовить сборочную среду на HA

### Сценарий A: Home Assistant OS / Supervised

1. В HA открыть **Настройки → Система → Информация**. Убедиться, что доступен Supervisor и приложения, записать режим установки, версию HA и свободные ресурсы VM.
2. Установить **ESPHome Device Builder** через **Настройки → Приложения (Apps)**, запустить, включить автозапуск и нажать **Open Web UI**.
3. В мастере создать устройство с именем **`formapanel-s0`**. Мастер может создать network/API/OTA автоматически — **сохранить сгенерированные значения**, прежде чем заменять конфигурацию.
4. Записать **версию Device Builder / ESPHome**. Зафиксировать состояние HA VM; ориентир — несколько GB свободного диска под toolchain и ~2–4 GiB памяти для первого ESP-IDF build (это запас для планирования, не гарантия требований).
5. Проверить резервное копирование `/config/esphome` (обычный путь при HA OS). **Настоящие ключи никогда не коммитить**.

### Сценарий B: HA Container без Supervisor

В таком режиме приложения HA могут отсутствовать. ESPHome Device Builder нужно запустить **как отдельный Docker контейнер на сервере/Proxmox**, см. [официальную установку](https://esphome.io/install/). Дальше работа через его Web UI аналогична, но реальный путь папки конфигурации будет зависеть от volume mapping. Не пытаться искать «Apps» там, где Supervisor отсутствует.

### Конфиденциальные настройки

Ссылки на локальные секреты в S0 YAML:

```yaml
# Локальный /config/esphome/secrets.yaml — только пример ключей
wifi_ssid: "YOUR_2_4_GHZ_SSID"
wifi_password: "YOUR_REAL_WIFI_PASSWORD"
formapanel_api_key: "GENERATED_VALID_BASE64_KEY"
formapanel_ota_password: "LONG_RANDOM_OTA_PASSWORD"
```

Ключ `formapanel_api_key` — **32-байтовый ключ в Base64**, использовать сгенерированный ESPHome, не произвольный пароль. Если wizard создал другие имена секретов, изменить ссылки `!secret` в YAML; не дублировать действующие credentials.

**Gate:** Device Builder открыт через HA/сервер, устройство создано, ключи локально сохранены, есть доступ к Validate/Build, внешние SDK-зависимости загружаются с сервера.

## 4. Этап S0-2: диагностический YAML (начать с одного файла в HA)

В файле `formapanel-s0.yaml` оставить **одну** копию каждой секции `wifi:`/`api:`/`ota:`. Перед заменой сохранить файл мастера для отката. Ниже — **предполагаемый, не проверенный компиляцией проекта** тестовый конфиг. GPIO и PSRAM актуальны для типового, но не гарантированно любого Guition.

```yaml
esphome:
  name: formapanel-s0
  friendly_name: "FormaPanel S0"

esp32:
  variant: esp32s3
  framework:
    type: esp-idf
  # После проверки физической flash можно установить:
  # flash_size: 16MB

psram:
  mode: octal
  speed: 80MHz

logger:
  level: DEBUG

api:
  encryption:
    key: !secret formapanel_api_key

ota:
  - platform: esphome
    password: !secret formapanel_ota_password

safe_mode:

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  power_save_mode: none

output:
  - platform: ledc
    id: panel_backlight_pwm
    pin: GPIO38
    frequency: 150Hz
    min_power: 0.01
    zero_means_zero: true

light:
  - platform: monochromatic
    id: panel_backlight
    name: "Display Backlight"
    output: panel_backlight_pwm
    restore_mode: ALWAYS_ON
    default_transition_length: 0s

i2c:
  id: panel_i2c
  sda: GPIO19
  scl:
    number: GPIO45
    ignore_strapping_warning: true
  scan: true

display:
  - platform: mipi_rgb
    model: GUITION-4848S040
    id: panel_display
    update_interval: never
    auto_clear_enabled: false

touchscreen:
  - platform: gt911
    id: panel_touch
    display: panel_display
    on_touch:
      - lambda: |-
          ESP_LOGI("touch", "x=%d y=%d", touch.x, touch.y);

debug:
  update_interval: 30s

sensor:
  - platform: debug
    free:
      name: "Free Internal Heap"
    block:
      name: "Largest Heap Block"
    psram:
      name: "Free PSRAM"
    loop_time:
      name: "Loop Time"

text_sensor:
  - platform: debug
    reset_reason:
      name: "Reset Reason"

lvgl:
  buffer_size: 25%
  pages:
    - id: diagnostics
      bg_color: 0x101820
      bg_opa: COVER
      widgets:
        - label:
            text: "FormaPanel S0"
            align: CENTER
            y: -65
            text_color: 0xFFFFFF

        - button:
            id: test_button
            text: "TOUCH"
            align: CENTER
            y: 75
            width: 200
            height: 80
            on_click:
              - logger.log: "LVGL button clicked"
              - lvgl.button.update:
                  id: test_button
                  text: "OK!"
```

**Что проверяется:** одноцветный фон, label, LVGL push button, координаты touch в логах, backlight через HA, свободные heap/PSRAM, reset reason, сеть и OTA.

**Почему этот YAML:** `mipi_rgb` с `GUITION-4848S040` — официальный preset, не нужно руками переносить большой RGB pin map; `lvgl.button.update` поддерживается для кнопки с `text:`; `debug` публикует free heap/largest block/PSRAM. При проблемах с логами учитывать, что определённые GPIO S3 могут использоваться платой: **не включать принудительно UART0 или USB Serial/JTAG без сверки схемы**. См. [LVGL widgets](https://esphome.io/components/lvgl/widgets/), [Debug](https://esphome.io/components/debug/).

### Если первый Validate/экран не работает — упрощение S0-2a

Чтобы отделить неисправность LCD/PSRAM от взаимодействий LVGL/GT911, временно **удалить блоки `touchscreen`, `debug`, `sensor`, `text_sensor` и заменить весь `lvgl:` на один ключ:**

```yaml
lvgl:
```

По [ESPHome LVGL](https://esphome.io/components/lvgl/) появится встроенная hello world/test screen. После успеха возвращать части последовательно:

```text
Wi-Fi/API/OTA + PSRAM
    → display + lvgl: (default test page)
    → GT911/I2C + touch logs
    → LVGL label + TOUCH button
    → debug sensors
    → OTA
```

Это временный диагностический путь, не отдельная версия FormaPanel.

### О памяти и PSRAM

На RGB565 480×480 full frame = **460 800 B / 450 KiB**. `lvgl.buffer_size: 25%` ориентировочно выделяет **115 200 B / 112.5 KiB** draw buffer, **но это не общая RAM**: RGB framebuffer, PSRAM, LVGL heap и Wi-Fi используют дополнительную память. На S0 не оптимизируем FPS: сначала проверяем наличие стабильного кадра. `safe_mode:` помогает при boot loop с доступным Wi-Fi/OTA, **но не заменяет восстановление по USB**.

## 5. Этап S0-3: Validate и сборка BIN на HA

1. **Edit → Save → Validate**. Сначала исправить первую конкретную ошибку схемы/версию. Не воспринимать приведённый YAML как прошедший тесты без реального Validate.
2. При успехе — **Install → Manual Download**. Первая сборка ESP-IDF может потребовать загрузки инструментов и cache, выполняется **на HA VM**, не на Windows.
3. Если предлагается выбор файла, для **первой USB-записи** использовать **Factory image** (с bootloader/partitions в поддерживаемом формате), а не OTA-only binary.
4. Скачать Factory BIN на Windows, зафиксировать его имя/размер, номер ESPHome и build log **без публикации секретов**.
5. Если Build fails из-за RAM/disk — увеличить ресурсы HA VM; если из-за CDN/PyPI/GitHub — проверить DNS/доступность *HA-сервера*, а не Windows; если из-за прошивки — проверить конкретный compiler error и секцию.
6. Не встраивать в S0 реальные HA lights/scripts. Устройство пока только диагностическое.

**Gate:** `Validate: PASS`; `Compile: PASS`; получен Factory BIN с воспроизводимыми version+config. Иначе **ничего не прошивать**.

## 6. Этап S0-4: первая USB-прошивка без SDK на ПК

1. Подключить Guition исправным USB **data** кабелем.
2. В Chrome/Edge открыть **https://web.esphome.io/**, нажать **Connect**, выбрать порт платы. Доступ к WebSerial зависит от браузера/OS и USB-UART.
3. Запустить установку скачанного **Factory** BIN, выбранного в `Install → Manual Download`. Если бинарник неподдерживаемого формата, не переходить к `erase all` без проверки.
4. Если устройства нет в портах — проверить кабель, питание, драйвер, USB interface. При необходимости ввести в bootloader **по инструкции именно этой платы** через BOOT/RESET.
5. Дождаться сообщения об успехе, перезагрузить, снять фото начального экрана.
6. Проверить, появляется ли `formapanel-s0` в DHCP/router и ESPHome Device Builder/HA integration. Первый старт после новой прошивки может занять больше времени.
7. При белом/чёрном дисплее **проверить, загрузилась ли сеть/логи**. Если сеть online, причина скорее в display/backlight/PSRAM, не обязательно в прошивальщике. Если устройство не загружается, использовать USB recovery.

**Gate:** первый показ `FormaPanel S0` + кнопка `TOUCH` (или базовый LVGL тестовый экран в режиме S0-2a), Wi-Fi/API доступны, три последовательных запуска без crash loops.

## 7. Этап S0-5: что и как проверить на физическом устройстве

| Test ID | Проверка | PASS-критерий | Доказательство |
|---|---|---|---|
| S0-H01 | 3 × power cycle и 3 × программный reset | Всегда стартует, нет watchdog/boot loops | logs + фото |
| S0-H02 | LCD 480×480, ориентация, однородность | Нет сбитой геометрии/полос/нестабильного изображения | фото |
| S0-H03 | 5 точек GT911: центр и 4 угла, касания у краёв | X/Y в ожидаемой системе координат, ~0…479, нет swapped/mirror | `touch` logs |
| S0-H04 | Нажать `TOUCH` | Меняется на `OK!`, log `LVGL button clicked` | logs + фото |
| S0-H05 | Wi-Fi, API, HA integration | Подключение, видны diagnostics entities | HA dashboard |
| S0-H06 | Изменить `Display Backlight` через HA | Яркость изменяется, экран возвращается в норму | фото/видео |
| S0-H07 | Heap/PSRAM после boot и 15–30 мин | Числа реалистичные, largest free block не обваливается | значения + timestamps |
| S0-H08 | Оставить панель на 30–60 минут | Нет reboot/WDT, touch/UI остаются отзывчивыми | uptime/log |
| S0-H09 | Прервать сеть/HA, затем вернуть | Устройство восстанавливает Wi-Fi/API, не зависает | timestamps |
| S0-H10 | Изменить `FormaPanel S0` на `FormaPanel S0 OTA` → Compile → Install по Wi-Fi | OTA завершён; новый текст на LCD; HA снова доступен | build log/фото |
| S0-H11 | После Git пакета: Validate/Build из remote refs | HA повторно собирает тот же UI | log + Git ref |

S0 не требует stress 24h, сложных анимаций и результатов p95/p99 FPS. Эти тесты относятся к S1 (см. [Performance](../06-validation/performance.md)).

### Таблица симптомов

| Симптом | Первые проверки |
|---|---|
| Чёрный экран, но online | GPIO38/подсветка, `mipi_rgb` model, PSRAM init |
| Полосы/смещения | RGB timing, orientation, версия ESPHome и hardware revision |
| LVGL показан, но touch молчит | I²C scan, GT911, GPIO19/45, питание/reset touch |
| Touch log есть, кнопка не реагирует | `touchscreen.transform` / orientation / координаты button |
| Кнопка работает, HA нет | 2.4 ГГц Wi-Fi, DHCP, mDNS, API port/firewall; подключить по IP |
| Reboot при LVGL init | PSRAM mode, draw/full framebuffer, largest free internal block, питание |
| После OTA устройство пропало | `safe_mode` при доступной сети, иначе USB recovery; проверить partitions и `flash_size` |
| Factory BIN не прошивается | file type, USB-UART driver, boot mode; не запускать вслепую full erase |

**Важная аппаратная неопределённость:** ориентация дисплея может потребовать `rotation` и `touchscreen.transform`, но **первый S0 намеренно не задаёт их**. Сначала измерить фактические координаты, затем менять соответствующие параметры.

## 8. Этап S0-6: GitHub Remote Packages после работающей OTA

После S0-H01…H10 извлечь из локального YAML **несекретную** основу в существующий публичный репозиторий:

```text
firmware/esphome/
  boards/guition-s3-480.yaml         # display, I2C/touch, PWM, PSRAM
  packages/s0-diagnostics.yaml       # LVGL test page, debug
  panels/s0-test.yaml                # packages+esphome name, БЕЗ credentials

docs/06-validation/
  guition-s0-results.md              # факты и фото/логи, БЕЗ секретов
```

Пока это **планируемые файлы**, они не добавлены данным документационным коммитом. Действующие секреты остаются только в HA. **ESPHome Git remote packages не могут использовать `!secret` внутри загруженного файла**; нужно передавать необходимые значения из локального YAML через substitutions или держать network/API/OTA **целиком локально**. [Документация Packages](https://esphome.io/components/packages/).

Пример будущей локальной конфигурации `/config/esphome/formapanel-s0.yaml`, **после создания `s0-test.yaml`**:

```yaml
substitutions:
  formapanel_node: "formapanel-s0"

packages:
  formapanel:
    url: https://github.com/exceptioncpp/FormaPanel
    ref: main
    files:
      - firmware/esphome/panels/s0-test.yaml
    refresh: 1h

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

api:
  encryption:
    key: !secret formapanel_api_key

ota:
  - platform: esphome
    password: !secret formapanel_ota_password
```

Удалённый пакет должен задавать имя устройства из substitution `formapanel_node`, но не включать локальные network credentials. После первого подтверждённого успешного Build закрепить tag или commit SHA вместо изменяемого `main`, учитывать Git cache/`refresh`. Настоящая конфигурация Device Builder может содержать другие ключи — не допускать конфликта/дублирования `api`/`wifi`/`ota` при слиянии.

**Gate:** удалённые пакеты читаются HA, проходят Validate, на сервере выполняется Build и OTA применяет обновление; локальные секреты **не попали в Git и downloadable CI artifacts**.

## 9. Шаблон фактического отчёта и checklist завершения

После испытаний создать `docs/06-validation/guition-s0-results.md` и **не отмечать PASS без измерения**:

```markdown
# FormaPanel S0 — фактический отчёт

- Дата/время, версия HA:
- ESPHome Device Builder / ESPHome / ESP-IDF versions:
- PCB revision, LCD/touch, USB interface:
- Flash/PSRAM согласно boot log:
- Исходная firmware + backup/recovery path:
- Конфигурация / commit SHA / BIN checksum:
- Validate / Build: PASS | FAIL
- USB Factory: PASS | FAIL
- LCD, touch coords, LVGL button: PASS | FAIL
- HA API, backlight: PASS | FAIL
- RAM: Free Heap / Largest Block / PSRAM Free:
- Power cycle / 30–60 минут stability:
- OTA: PASS | FAIL
- Git Remote Package Validate/Build: PASS | FAIL
- Фото/скриншоты/логи (без secrets):
- Блокеры и точные шаги воспроизведения:
- Решение: READY FOR S1 | NOT READY
```

**Exit checklist:**

- [ ] Установлен Device Builder на HA/сервере (без SDK на Windows).
- [ ] Есть проверенная процедура USB recovery и данные ревизии.
- [ ] Скомпилирована и установлена S0 Factory-прошивка.
- [ ] Успешны дисплей, touch, кнопка, подсветка, HA API и память.
- [ ] Нет очевидных boot loops и критических утечек на коротком тесте.
- [ ] Успешно выполнено **реальное OTA** с обновлённой надписью.
- [ ] Из Git Remote Package получен повторно валидируемый Build.
- [ ] В репозитории есть **отдельный фактический** отчёт S0.

## 10. Дальше: S1 → RH-01 → CI

**S1 UI Performance PoC:** собственные 480×480 фоны, русские glyphs Nunito/Comfortaa, две картинки RGBA LA-01, отдельный touch hitbox, 2–3 pages и переходы, замеры internal heap/PSRAM, RGB565 banding, frame time и touch latency. Только после этого — полноценный [RH-01](../03-design/room-home-reference-RH-01.md) и [LA-01](../03-design/light-action-reference-LA-01.md) с HA entities и общими профилями комнат.

**GitHub Actions:** добавить после первого успешного HA local build и Remote Package. Тогда CI сможет проверять уже испытанную S0/S1 конфигурацию и генерировать BIN, без параллельной отладки двух разных build environments. Сравнение native ESP-IDF остаётся в [ADR-0003](../04-architecture/adr/0003-platform-evaluation.md) и [A/B-протоколе](../06-validation/rh01-platform-ab-test.md).

## Первоисточники

[ESPHome Install](https://esphome.io/install/) · [Getting Started](https://esphome.io/install/getting-started/) · [FAQ/Manual Download](https://esphome.io/guides/faq/) · [Guition profile](https://devices.esphome.io/devices/guition-esp32-s3-4848s040/) · [MIPI RGB](https://esphome.io/components/display/mipi_rgb/) · [GT911](https://esphome.io/components/touchscreen/gt911/) · [LVGL](https://esphome.io/components/lvgl/) · [Widgets](https://esphome.io/components/lvgl/widgets/) · [Debug](https://esphome.io/components/debug/) · [Safe Mode](https://esphome.io/components/safe_mode/) · [Remote Packages](https://esphome.io/components/packages/) · [ESPHome Web](https://web.esphome.io/) · [ESPHome 2026.10.1 release](https://github.com/esphome/esphome/releases/tag/2026.10.1).
