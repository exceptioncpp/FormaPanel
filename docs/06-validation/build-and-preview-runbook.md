# От checkout к Validate, native preview и BIN

Операционный срез **01.11.2026**: установленный **FormaPanel Workshop 0.1.1**,
**ESPHome 2026.10.1 / LVGL 9.5.0 / ESP-IDF 5.5.6**, HA Core **2026.10.4**.
Документ описывает повторяемую работу на существующем HA. SDK на Windows
не требуется. Источник установки — `tools/ha-workbench/` в доверенной ревизии
репозитория; игнорируемые `reports/local/*` helpers для восстановления не нужны.

## 1. Получить рабочий checkout

В Studio Code Server открыть `/config/esphome/formapanel-rh01` либо
`FormaPanel.code-workspace` в нём. Это основной Git checkout, который Workshop
читает как `/homeassistant/esphome/formapanel-rh01` через read-only mount.
Worker не создаёт отдельную редактируемую копию UI.

На **чистом, ещё не существующем** целевом пути можно клонировать репозиторий:

```sh
git clone https://github.com/exceptioncpp/FormaPanel.git /config/esphome/formapanel-rh01
git -C /config/esphome/formapanel-rh01 status --short
git -C /config/esphome/formapanel-rh01 branch -vv
```

Выбранный commit обязан содержать `tools/ha-workbench`, manifest профилей,
entry YAML, PNG и TTF. Исторический `580f594` сам по себе новую мастерскую не
содержит: при первоначальном развёртывании новые файлы оставались в working
tree, push не выполнялся. Сначала сохранить/версионировать нужный рабочий набор;
отсутствие новых файлов в старом remote commit не исправляется копированием
одного YAML. Не клонировать поверх существующих незакоммиченных изменений.

Доверие IDE разрешать для точного каталога проекта. Git diff/commit/pull/push
выполняются владельцем после просмотра изменений; Workshop Git не публикует
и GitHub credentials не переносит. Будущие изменения между компьютерами и HA
передавать через Git, не повторным bootstrap overlay.

Проверить состав:

```text
config/workbench-targets.json
firmware/esphome/{formapanel-rh01.yaml,targets/,profiles/,packages/,boards/,previews/}
assets/generated/480x480/rh01-*.png
assets/source/fonts/Nunito-{Bold,Medium}.ttf
tools/ha-workbench/{config.yaml,build.yaml,Dockerfile,server.py,web/}
```

Если HA app ещё не установлен, следовать [инфраструктурной инструкции](../../../../docs/infrastructure/ha-formapanel-workshop.md):
из репозиторного `tools/ha-workbench` подготовить local app context, reload
store/install, при необходимости заполнить private toolchain cache и запустить
Workshop с Ingress. Это однократная установка worker, не перенос проекта
между редактором и сборщиком при каждой правке.

## 2. Восстановить private secrets и проверить пути

Секреты аппаратного entry находятся в
`firmware/esphome/packages/secrets.yaml`, рядом с `packages/connection.yaml`:
`wifi_ssid`, `wifi_password`, `formapanel_api_key`, `formapanel_ota_password`.
Взять их из приватного backup/хранилища и сохранить с правами `0600`.
API key — 32-byte Base64 ESPHome key. Не печатать файл и не добавлять в Git.

ESPHome разрешает `!include` относительно включающего YAML; `!secret` ищется
рядом с пакетом с fallback к основному config. Главный worker wrapper находится
в private `/data/configs`, поэтому общего `/config/esphome/secrets.yaml`
может не хватить. Host preview network-free и secrets не использует.

`formapanel_asset_dir` в entry позволяет работать с относительными assets при
обычном запуске из дерева проекта. Worker переопределяет его абсолютным
`/homeassistant/esphome/formapanel-rh01/assets`, а также задаёт отдельные
`preview_build_path`, `formapanel_build_path` и `esphome.build_path`.
Не переписывать вручную пути всех image/font файлов под каждый job.

Проверить Git ignore для реального `secrets.yaml` и видимость настоящих
`firmware/esphome/previews/*.yaml`. Если сохранились старые runtime-папки,
их private exclusions в `.git/info/exclude` должны быть корневыми:
`/.bootstrap/`, `/native-data/`, `/native-output/`, `/previews/`, `/logs/`.
Шаблон `previews/` без начального `/` ошибочно скроет вложенные исходные preview.

## 3. Выбрать профиль и правильный entry

Список Workshop читается из `config/workbench-targets.json`:

| ID | Firmware entry | Native entry | Явно снимаемые кадры |
|---|---|---|---|
| `rh01` | `firmware/esphome/formapanel-rh01.yaml` | `firmware/esphome/previews/host-rh01.yaml` | lamp on/off |
| `living` | `firmware/esphome/targets/living.yaml` | `firmware/esphome/previews/living.yaml` | on/off и общий info |
| `bedroom` | `firmware/esphome/targets/bedroom.yaml` | `firmware/esphome/previews/bedroom.yaml` | on/off и общий info |

Room profiles выбирают общие `rh01-ui.yaml` / `info-page.yaml` и меняют
substitutions. Device entry добавляет board/network/diagnostics, host entry —
snapshot backend. Один профиль не должен подключать home package дважды.

В расширении IDE для `profiles/bedroom.yaml` допустимо предупреждение о том,
что validation не выполняется без `esphome:`: это package. Проверять нужно
`targets/bedroom.yaml` либо кнопкой Workshop. Не дописывать `esphome:` в общий
package только ради удаления подсказки IDE.

Новый профиль: добавить room config, пару firmware/preview entry и строку в
manifest, затем обновить UI Workshop. Worker читает manifest заново; для нового
профиля app rebuild не нужен. ID профиля: `[a-z0-9_-]`, до 48 символов, уникальный.

## 4. Три операции Workshop

В HA открыть **FormaPanel Workshop**, выбрать профиль. При сохранении source
preview автоматически **не запускается**; каждый раз нажать нужную кнопку.
Работает одно задание одновременно, конкурирующий запрос получает HTTP 409.

### Проверить

Кнопка **Проверить** выполняет `esphome config` для настоящего firmware entry
через служебный wrapper. Ожидается завершённый job и `ESPHome configuration:
PASS`. Это проверяет schema/IDs/packages и ссылки на resources/secrets, но **не компилирует**
C++ и не подтверждает запуск на плате. Отдельный native entry проходит свою
config validation при операции preview.

### Обновить предпросмотр

Кнопка **Обновить предпросмотр** валидирует native entry, компилирует host
программу, запускает её и сохраняет BMP через `snapshot.take`, затем PNG.
Это реальные пиксели ESPHome/LVGL, включая локальные TTF и alpha.
Ожидаются завершённый job, нужные кадры и отсутствие отметки stale после
сборки текущих исходников. Открыть каждый кадр и проверить значения, язык,
обрезку, состояния и общие страницы.

**Новая страница сама не снимется.** Добавить в capture-сценарий переход
`lvgl.page.show`, дождаться flush/заданной паузы и выполнить `snapshot.take`
с уникальным filename. У комнат backend `previews/room-backend.yaml`, у RH-01
отдельный `host-rh01.yaml`. Сохранить INFO marker
`RH01_NATIVE_PREVIEW_COMPLETE`: по нему worker завершает native процесс.
Нынешний контракт использует `rh01_home`, `rh01_lamp_image`, `rh01_lamp_on`,
`rh01_lamp_off`, `panel_info`. Другой home должен сохранить эти ID или получить
свой capture backend. Обычный PNG viewer не интерактивный touch-эмулятор.

### Собрать прошивку

Кнопка **Собрать прошивку** валидирует аппаратный entry и выполняет
`esphome compile`. После успеха предлагает `firmware.factory.bin` и
`firmware.ota.bin` с размером и SHA-256. Проверить профиль, дату/job, source
и успешный статус прежде чем выбирать файл для установки. Factory и OTA
имеют разное назначение; Workshop **не запускает upload/OTA** и не прошивает
подключённые устройства. Аппаратная установка/проверка — отдельный этап.

Последние успешные файлы сохраняются после последующих ошибок. Старые BIN
и PNG не считать результатами неудачного нового job. Смена source может
пометить прошлый preview stale; fingerprint охватывает общие firmware/assets/config,
поэтому изменение другого общего пакета также может потребовать пересборки.

## 5. Где cache, metadata, job log и downloads

В source checkout worker не пишет. Его private volume:

```text
/data/configs/<kind>-<profile>.yaml         # стабильный wrapper
/data/esphome/<kind>/<profile>/            # стабильные ESPHome metadata
/data/cache/{idf,host,platformio}/          # toolchain/cache, не source
/data/build/preview-/<profile>/            # native build
/data/build/firmware-/<profile>/           # аппаратный build
/data/jobs/<job-id>/build.log
/data/jobs/<job-id>/job.json
/data/jobs/<job-id>/snapshots/*.bmp
/data/jobs/<job-id>/*.png
/data/jobs/<job-id>/firmware*.bin
/data/result-<profile>-{preview,firmware}.json
```

Журнал пользователь читает в Workshop UI. Все `/data` выше относятся именно
к контейнеру Workshop, а не к одноимённому каталогу Studio Code Server.
Административный host path этого volume:
`/mnt/data/supervisor/apps/data/local_formapanel_workbench` на HA OS.
Не искать build cache внутри read-only source checkout.

`kind` — `validate`, `preview` или `firmware`. Начиная с **0.1.1** wrapper и
`ESPHOME_DATA_DIR=/data/esphome/<kind>/<profile>` стабильны между заданиями.
Меняются job output folders, а не identity metadata. Простого сохранения одной
build-папки для incremental compilation недостаточно. На 0.1.0 per-job wrapper/
metadata могли провоцировать clean; первый прогон после перехода на 0.1.1
заполняет новые metadata и не сравнивается с тёплыми повторами.

Окружение задаёт `ESPHOME_ESP_IDF_PREFIX=/data/cache/idf`,
`ESPHOME_HOST_PREFIX=/data/cache/host`; `ESPHOME_IS_HA_ADDON` удаляется.
`ESPHOME_SNAPSHOT_DIR=/data/jobs/<id>/snapshots` уникален, потому что snapshot
не перезаписывает файлы. Host executable обычно находится внутри build в
`.pioenvs/<esphome.name>/program`.

UI получает состояние через относительный `api/state?profile=...`, запускает
job через `POST api/jobs`; downloads — `files/<job-id>/<artifact>` за HA Ingress.
Не сохранять сессионный Ingress URL как постоянный адрес и не открывать host
порт ради загрузки. BIN содержат device credentials; хранить их приватно.

Проверенный срез RH-01 01.11: без изменения 6.19 с, clock x29→31 7.88 с,
возврат x29 6.64 с (validate + compile + render на сервере). Повторные jobs без
clean, по два PNG, возврат кадра побитно идентичен. Cold run исключён,
браузерный polling добавляет до 2 с; fonts/assets и другая композиция могут
потребовать больше времени. Это измеренный пример, не срок любого нового UI.

## 6. Повторение проверки, recovery и обновление app

| Ситуация | Действие |
|---|---|
| Нет профилей | Проверить mount `/homeassistant`, option workspace, manifest и существование обоих entry |
| Missing include/font/image/secret | Проверить дерево checkout, asset substitution, package-relative secret path; один скопированный entry не заменяет репозиторий |
| Config PASS, compile FAIL | Читать первую ошибку компилятора в job log; config не проверяет весь generated C++ |
| Новый экран не появился | Добавить явный capture phase в соответствующий backend |
| Capture job не завершается | INFO completion marker, верные IDs, два кадра минимум, новый snapshot output dir |
| Повторно clean каждый раз | Installed version ≥0.1.1, стабильные configs и ESPHOME_DATA_DIR; не менять cache identity на каждый job |
| HTTP 409 | Дождаться текущего job, не запускать несколько сборок в обход UI |
| Stale или прежние файлы после ошибки | Исправить source и успешно пересобрать выбранный профиль; не принимать старый artifact за новый |

Перед вмешательством сохранить `job.json` / `build.log`, точный профиль,
commit/dirty state и источник ошибки. Не начинать с удаления всего `/data`.
При app restart успешные result JSON/артефакты сохраняются в private data,
но новый preview всё равно должен соответствовать текущему source.

Изменения YAML/PNG/TTF/manifest читаются прямо из checkout — app update не нужен.
Если меняется source **самого worker**, обновить только local app build context
из Git `tools/ha-workbench` по [infra runbook](../../../../docs/infrastructure/ha-formapanel-workshop.md).
При прежнем `version` допустим rebuild; при version bump нужны команды на
HA OS host:

```sh
ha store reload --raw-json
ha apps update local_formapanel_workbench --raw-json
```

`rebuild` не обновляет installed version в Supervisor. Проверить app version
в HA и повторить config/native/BIN smoke. Перезапуск HA Core не нужен.

До update/restore сохранить Git историю **и uncommitted/untracked source**,
private secrets отдельно и app `/data`/options при необходимости. Backup одного
app не равен backup source: checkout находится в отдельном read-only mount.
Для source regression — review/Git revert и обычные проверки. Для сбоя worker —
восстановить доверенный app backup либо исправленный versioned app source и
выполнить штатный update. Реальный downgrade в этой среде не испытывался;
не считать rebuild подтверждением отката installed version.

## 7. Локальные проверки и реальные границы CI

В подготовленном Python-окружении с `tools/requirements.txt`, либо в CI:

```sh
python tools/validate.py
python -m unittest discover -s tests -v
git diff --check
```

Здесь нет установки ESP32 SDK на Windows. Если зависимости Python ещё не
подготовлены, использовать существующий CI/подготовленную среду, а не ставить
SDK ради этих проверок. Изменённые исходные art resources должны пройти
детерминированные render commands и review полученных файлов.

Фактический `.github/workflows/verify.yml` выполняет: Python 3.12, install
`tools/requirements.txt`, `render_assets.py --all`, `render_rh01.py`,
`validate.py`, unittest. Это **asset/static/unit CI**, а не ESPHome config,
native compile/render или firmware build. Успешный GitHub check не заменяет
три операции на HA и не подтверждает touch, LCD timing, PSRAM или OTA.
Tests с mocked subprocess проверяют контракт worker, не являются сборкой платы.

Для нового варианта повторить Validate, native кадры ожидаемых состояний и
firmware build именно этого профиля. Финальную OTA и аппаратные испытания
планировать отдельно; live HA entities/actions в нынешних демо не настроены.

Связанные документы: [методика разработки UI](../02-research/effective-ui-development-2026-11.md),
[общий браузерный workflow](../02-research/ha-browser-workflow.md),
[первичная приёмка](ha-workshop-2026-10-31.md),
[native доказательство](rh01-native-preview-2026-10-31.md).
