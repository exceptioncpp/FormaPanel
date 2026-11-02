# Functional UI: доступ к сборкам, 01.11.2026

Только read-only проверка транспорта выполнена в рамках этого отчёта. Source на HA не менялся, новые jobs не запускались, устройства/OTA не затронуты.

## Подтверждённый доступ

Из `D:\Work\Projects\Home` доступен SSH alias `home-pve` с проектным `local/keys/ssh_config`; далее QEMU guest agent VM200 и `docker exec`. Дополнительных прав не потребовалось. HA Workshop installed/latest **0.1.1**, state **started**, ESPHome **2026.10.1**. Worker container `app_local_formapanel_workbench`. Loopback API внутри него доступен на `http://127.0.0.1:8099`; открывать host port или сохранять Ingress URL не требуется.

Проверенный вспомогательный transport: `reports/local/build_ha.py` функции `python_in(container, code, data=None)` и `guest(argv, data=None)`. Импорт не выполняет deploy/build. Это игнорируемый локальный helper, не переносимая основа установки. Не запускать его `deploy`: прежний bootstrap не делает требуемый backup/CAS.

Пример **read-only** из корня FormaPanel:

```python
import sys, json
sys.path.insert(0, 'reports/local')
from build_ha import python_in
from workbench_smoke import request
print({k: request('/api/state?profile=living')[k] for k in ('git', 'profiles')})
print(python_in('app_local_formapanel_workbench',
    "import subprocess; print(subprocess.check_output(['esphome','version'],text=True).strip())"))
```

Не печатать полный `ha apps info`: он содержит временные Ingress поля. Для версии разбирать JSON в памяти и выводить только `version/version_latest/state`.

## Source baseline и точечная доставка

HA checkout при проверке: branch `main`, commit `580f594`, dirty. Worker читает `/homeassistant/esphome/formapanel-rh01`, writable через container `homeassistant` как `/config/esphome/formapanel-rh01`.

В момент проверки совпали SHA256 Windows/HA: manifest, living target/preview/profile, room-backend, server.py. `packages/rh01-ui.yaml` уже различался; HA hash `c4a86595045dd10d97fac02b2ab728a55aeba6d0542683436bdebefe624f73fc`. Это observation, не разрешение перезаписать расхождение.

Для всех **явно выбранных owned файлов** отправить через `python_in('homeassistant', code, json_payload)` список relative paths. Remote code делает `resolve()`, проверяет `is_relative_to(root)`, исключает `.git`, secrets и private/runtime dirs, возвращает только `{path: sha256-or-null}`. Передача JSON через stdin поддерживается `qm guest exec --pass-stdin 1`; source/credentials не вклеиваются в shell. Большие ответы делить на bounded batches (guest-agent output capped).

После review различий согласованный payload на каждый файл содержит `path`, `expected_old_sha256` (null только для действительно нового), `new_sha256`, Base64 bytes. Алгоритм доставки:

1. Проверить все old hashes перед любыми изменениями; несовпадение — остановить, перечитать/review, не force.
2. Создать отдельный timestamp backup вне includes, например `/config/esphome/formapanel-functional-backups/<UTC>/`; сохранить прежние bytes и manifest старых/новых hashes, отметить ранее отсутствовавшие файлы.
3. Для каждого файла повторить CAS old hash непосредственно перед записью; проверить decoded new hash; временный sibling файл и atomic `os.replace`; существующий mode сохранить.
4. Сверить весь delivered manifest и Git status; записать evidence. При частичном сбое остановиться, не запускать jobs, восстановить только уже изменённые owned файлы, проверяя current hash == delivered hash.

Не переносить весь Windows tree, не менять secrets, не обновлять `.bootstrap/provisioned.json`, не делать reset/clean. Backup + expected hash обязательны даже при исходном совпадении.

## Workshop Validate/native/BIN после доставки

Следующие команды — **предстоящие**, не выполнены этим аудитом. Из корня FormaPanel:

```powershell
python reports/local/workbench_smoke.py validate living
python reports/local/workbench_smoke.py preview living
python reports/local/workbench_smoke.py firmware living
```

Проверенный helper выполняет loopback `POST /api/jobs` с `{kind,profile}`, затем `GET /api/state?profile=living`; сериализовать jobs, 409 означает занятость. Уточнить helper при конкурентном запуске: polling должен сверять исходный `job.id`, а не принять любой последующий глобальный job. Он сохраняет JSON в `reports/local/workbench-smoke/living-<kind>.json`.

Точный worker путь: `/data/configs/<kind>-living.yaml` включает actual target/preview; `esphome config`, затем для preview/firmware `esphome compile`. Native executable запускается до `RH01_NATIVE_PREVIEW_COMPLETE`, snapshot BMP → PNG. Требовать все ожидаемые capture filenames нового сценария, не только worker минимум >=2. Firmware требует оба `firmware.factory.bin` и `firmware.ota.bin`, хотя worker считает успехом >=1. Отдельно сверять current source fingerprint, job ID/status и отсутствие stale; прежние PNG/BIN после failure не принимать.

Evidence: `/data/jobs/<id>/{job.json,build.log,*.png,firmware*.bin}` внутри worker; downloads `/files/<id>/<name>` доступны через существующий API transport/Ingress. BIN приватны. Не печатать их bytes/Base64. Для извлечения использовать bounded binary chunks и SHA256, как read-only fetch pattern в helper, но с **Workshop** job paths, а не прежними Device Builder paths. Никакой команды upload/OTA.
