# HA Workshop: общий Git checkout и сборка, 2026-10-31

Развёрнута **FormaPanel Workshop 0.1.0**: локальное HA приложение с Ingress,
которое читает тот же Git checkout, что редактирует Studio Code Server.
Передачи проекта между редактором, preview и сборщиком нет.

## Фактические пути

| Назначение | Путь / значение |
|---|---|
| Общий checkout в Studio Code Server | `/config/esphome/formapanel-rh01` |
| Тот же каталог в Workshop | `/homeassistant/esphome/formapanel-rh01`, read-only |
| Общий bind на HA OS | `/mnt/data/supervisor/homeassistant` |
| Git origin | `https://github.com/exceptioncpp/FormaPanel.git` |
| Ветка / upstream | `main` / `origin/main` |
| Исходный commit | `580f594`; новые файлы и изменения пока не закоммичены |
| HA app slug | `local_formapanel_workbench` |
| Worker container | `app_local_formapanel_workbench` |
| Local app source | `/mnt/data/supervisor/apps/local/formapanel_workbench` |
| Приватные cache, jobs, BIN и PNG | `/data` внутри Workshop |

Studio Code Server уже был установлен: приложение **7.2.0**,
code-server **4.139.1 / Code 1.139.1**, Git **2.47.3**.
В редакторе нужно открыть папку `/config/esphome/formapanel-rh01`
или лежащий в ней `FormaPanel.code-workspace`. Глобальные настройки и
исходная папка пользовательского IDE не менялись.

Первичное развёртывание сохранило историю Git и 137 файлов проекта,
проверенных SHA-256. Настоящий `secrets.yaml` сохранён, имеет права `0600`
и игнорируется Git. Дополнительные runtime-каталоги исключены только
корневыми шаблонами `.git/info/exclude`; исходные вложенные `previews/`
остаются видимыми в Source Control.

Windows checkout остаётся исходной резервной копией. После начала работы
в HA изменения между рабочими местами передаются Git, а не повторным
наложением файлов из bootstrap-помощника. GitHub push не выполнялся;
учётные данные GitHub не копировались и новые ключи доступа не создавались.
Вход для будущего push пользователь выполняет средствами IDE/Git.

## Сборщик и доступ

Приложение использует уже имевшийся официальный образ
`ghcr.io/esphome/esphome-hassio:2026.10.1`
(`sha256:f850cb7f2b170d4bde07637cffb22f266317fac87f3747f2898764a752fa29e5`).
Фактический стек: **ESPHome 2026.10.1 / LVGL 9.5.0 / ESP-IDF 5.5.6**.
Первично скопированы существующие toolchain caches в приватный `/data`:
IDF около 5 GiB, host около 14.3 MiB. Исходный Device Builder сохранён.
Windows SDK и новые системные зависимости на Windows не устанавливались.

Workshop имеет read-only source mount, не получает Docker socket,
Supervisor API и Home Assistant API. Контейнер не privileged,
опубликованных host ports нет (`ports={}`). Доступ к UI и результатам
идёт через авторизованный HA Ingress; пункт sidebar включён.
Сборка выполняется последовательно, физическое устройство не прошивается.

`config/workbench-targets.json` объявляет RH-01, гостиную и спальню.
Worker читает настоящие entry YAML и все их `packages`/`!include`,
а промежуточный job wrapper задаёт только абсолютные пути assets/build.
Шрифты, изображения и общие подэкраны берутся прямо из checkout.
Изменение общего YAML было подхвачено следующим заданием без перезапуска
приложения и без повторной доставки проекта.

## Проверки установленного приложения

| Проверка | Результат |
|---|---|
| Firmware config RH-01 | PASS |
| Firmware config гостиная | PASS |
| Firmware config спальня | PASS |
| Native preview гостиная | PASS: три PNG `info`, `rh01-on`, `rh01-off`, 480×480 |
| Native preview спальня | PASS: три PNG из сохранённого профиля, 480×480 |
| Native preview RH-01 в Workshop | PASS: два состояния лампы, 480×480 |
| ESP32 firmware гостиная | PASS: Factory и OTA BIN |
| Загрузка трёх PNG и двух BIN через HTTP worker | Все HTTP 200 |
| PNG | Все успешно декодируются; три состояния различаются |
| BIN | Размеры и SHA-256 скачанного содержимого совпадают с metadata job |
| Общий checkout после сборки | Все 137 исходных SHA-256 совпадают, source не изменён |
| Кириллица общего info-подэкрана | Визуально проверена на настоящем LVGL PNG |

В браузере проверен полный рабочий цикл: в Studio Code открыт настоящий
`firmware/esphome/profiles/bedroom.yaml`, время изменено с `23:10` на `23:11`
и сохранено. Следующее задание Workshop показало кадр `23:11` без доставки
или импорта проекта. Затем исходное `23:10` восстановлено, сохранено и
повторно собрано; итоговый кадр содержит `23:10`, `21°`, `48%`, `620 ppm`.
Базовый RH-01 также собран через UI Workshop и доступен при первом открытии.
Git-панель Studio Code активна после согласованного доверия только каталогу
проекта. После доставки финальных документов проверены SHA-256 139 файлов;
сборщик не изменил исходники. Локально проходят все 10 тестов и validator.

Артефакты гостиной:

| Файл | Bytes | SHA-256 |
|---|---:|---|
| `firmware.factory.bin` | 1 671 776 | `1b3035787b1e541618d5ebca71bdabab77ba8dd173ffa2d61379d0db1a15da08` |
| `firmware.ota.bin` | 1 606 240 | `69627d2c3fb9bcf07df5cc430882ae31152463ed030306df78e37c6410c970ab` |

Приватные протоколы API и проверки сохранены локально в
`reports/local/workbench-smoke/`; первичный source manifest —
`reports/local/ha-bootstrap/source-manifest.json`.
BIN содержат credentials устройства, поэтому остаются приватными.
Оценка flash/RAM сборки не заменяет испытания физического дисплея,
touch, PSRAM, Wi-Fi/API и OTA.

После проверки HA Core, ESPHome Device Builder, Studio Code Server и
Workshop имеют состояние `running`. На HA осталось около 34.5 GiB диска
и 2.6 GiB RAM available. HA не перезапускался.

Для отключения новой мастерской достаточно остановить только
`local_formapanel_workbench`; общий checkout и прежние приложения
при этом сохраняются. Сеть и глобальная HA configuration не менялись.
