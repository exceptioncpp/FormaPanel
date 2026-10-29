# Home Assistant integration contract (draft)

## Общие категории входных сущностей

- `time` — локальное время панели/HA/NTP, источники уточнить при интеграции.
- `room_temperature`, `room_humidity` — собственное помещение.
- `outdoor_weather`: `condition`, `temperature`, возможно `forecast` и `wind`, из HA.
- `light_primary`: HA entity или script/scene для ручного света комнаты.
- `light_groups`: список HA lights/groups для `lighting`.
- `climate_room`: климатическая сущность или явно составной controller на HA.
- `heating_season`: optional HA `input_boolean` / schedule / другой автоматический признак; **панель не вычисляет сезон**.
- `bathroom_floor`, `bathroom_vent`, `bathroom_towel_timer`: набор HA сущностей и скриптов, конкретные имена пока неизвестны.
- `master_lighting`: действие HA для прихожей, семантику уточнить.

## Конкретные команды (draft)

| Event from panel | Intended HA action | State feedback |
|---|---|---|
| tap primary room light | `light.toggle` / script | обновлённая сущность/состояние сцены |
| change light brightness | `light.turn_on` with brightness | обновлённый brightness |
| change climate setpoint | `climate.set_temperature` либо скрипт | подтверждённый setpoint |
| start towel timer | `script.turn_on` c параметром duration / `timer.start` | active state + remaining |
| tap master lighting | конкретный HA script/scene | состояние группы/сцены |

Важное ограничение: «мастер освещения» и кнопка ручного света должны учитывать внешнюю HA автоматику; нельзя выбрать service без проверки реальной схемы.

## Передача состояний

1. Дата обновления, стейт, units, источник.
2. Когда HA ещё не ответил, показать `pending` ограниченное время (значение уточнить тестом).
3. Когда действие завершилось ошибкой/HA недоступен — показывать текущий state и unobtrusive error.
4. Отображать отдельно `outdoor` и `room`, особенно если обе температуры видны одновременно.

## Безопасность

API keys, HA access tokens, Wi-Fi passwords, сертификаты — `secrets.yaml`/защищённые локальные файлы, не репозиторий. Разрешение `Allow the device to perform Home Assistant actions` настраивается отдельно для каждой панели.

## Contract-first testing

Создать mock entity-state events для каждого класса widget и проверить UI без реальных реле. Затем smoke test через выделенные безопасные HA test helpers/script до управления настоящими устройствами.
