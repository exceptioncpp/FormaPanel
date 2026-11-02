# Фактическая HA инвентаризация для функционального UI

Срез: **01.11.2026, 11:06–11:16 МСК**. Только чтение; HA, устройства и source не изменялись, бытовые service calls не выполнялись. Это инвентаризация, не реализация и не разрешение на управление нагрузками.

## Доказательства и ограничения

- **E1 — текущие файлы на HA VM200**, прочитанные через закреплённый SSH alias `home-pve` → QEMU guest agent → container `homeassistant`: `/config/configuration.yaml`, `/config/packages/home_climate.yaml`, `/config/automations.yaml`, `/config/scripts.yaml`, `/config/.storage/core.entity_registry`, `/config/.storage/core.device_registry`. Физический корень HA OS подтверждён чтением `/mnt/data/supervisor/homeassistant`. `configuration.yaml` включает `packages`; отдельный `automations.yaml` содержит `[]`, `scripts.yaml` пуст. Это НЕ означает отсутствие автоматик: климатические находятся в package.
- **E2 — текущий Recorder**, SQLite URI `file:/config/home-assistant_v2.db?mode=ro`, последние записи по entity ID с join `states_meta` / `state_attributes`. Чтение 08:09–08:10 UTC. Данные продолжают записываться, но это **последняя записанная история, не подтверждение текущего API state**. Старый `last_updated_ts` постоянного helper не доказывает недоступность. Recorder может не сохранять все capability attributes.
- **E3 — неудачные чтения ошибочно выбранного порта около 11:06–11:08 МСК**: GET Supervisor `/core/api/states` → HTTP 401; GET `192.168.0.123:8123/api/states` и `127.0.0.1:8123/api/states` внутри HA container → connection refused. Доступ не ремонтировался. По этим ошибкам нельзя заключать, что HA/сущности отсутствуют. Последующий Recorder подтверждает свежие записи. Адрес :8123 был предположением и не фактическим endpoint; успешная проверка документированного HTTP/80 приведена в E5 ниже. WebSocket не проверен.
- **E4 — репозиторий инфраструктуры**: `climate/README.md`, `climate/homeassistant/room-sources.json`, `climate/esphome/room-climate.yaml`, `docs/changes/climate-ha-setup-2026-10-23.md`, `docs/infrastructure/ha-formapanel-workshop.md`. Источник поведения TPI и защит; актуальный package E1 сопоставлен с этим описанием.

Registry и полная таблица Recorder metadata просмотрены для всех `light`, `switch`, `climate`, `timer`, а также температурных/влажностных/погодных сущностей. **Не найдены в просмотренном registry/Recorder** не равно «физически отсутствуют». Неизвестные ID ниже намеренно не заменены предположениями.

## Living — первый обязательный профиль

Следующие таблицы сохраняют исторический срез E1/E2 11:09 МСК; актуальный live срез E5 ниже имеет приоритет. Для неразрешённых slots live availability не установлена; `unknown/unavailable`, отсутствие подтверждения или устаревший образец должны отражаться в UI, а не превращаться в 0/OFF. Будущие команды ниже описывают контракт, ни одна не отправлена.

| Slot | Фактическая entity / attribute / unit и capabilities | Последний Recorder / freshness | Будущий command и feedback | Автоматика / evidence |
|---|---|---|---|---|
| Основной свет | **ID не установлен**. Единственные найденные `light.*` — `light.guition_esp32_4848s040_display_brightness` и `light.guition_esp32_4848s040_screensaver_brightness`; это дисплей, не свет комнаты. Brightness/цветовые возможности основного света неизвестны | Обе служебные lights записаны `unknown`; бытовой feedback отсутствует | Ровно один toggle в согласованный HA light/script; сразу открыть Lighting; pending до подтверждённого HA state, timeout/error не подменяет state | Living lighting automation и ручной override не обнаружены в просмотренных HA YAML/registry. До разрешения точной нагрузки и override команды блокированы. E1/E2 |
| Температура воздуха | `sensor.home_living_temperature`, state °C; attributes `sources`, `sample_time`, `valid_sources`, `freshness_entity`, `spread_c`; read-only. Source `sensor.bthome_sensor_ff38_temperature` | 26.28 °C; `sample_time=2026-11-01T11:09:30.189213+03:00`, `valid_sources=1` | Только чтение; использовать sample_time/availability, не возраст изменения числового значения | HA медиана свежих комнатных датчиков; floor/wall исключены. E1/E2/E4 |
| RH | `sensor.home_living_humidity`, state %, `sources`, `sample_time`, `valid_sources`; source `sensor.bthome_sensor_ff38_humidity` | 49.57%; sample_time 11:09:33 МСК; valid_sources=1 | Только чтение; показывать stale/нет данных | E1/E2/E4 |
| Свежесть BLE | `sensor.bthome_sensor_ff38_packet_id` — фактический ID из room-sources и template `freshness_entity` | Последняя запись Packet ID в Recorder старая (23 октября); одновременно свежие aggregate samples с valid_sources=1. Это **не основание** объявлять BLE stale: требуется live `last_reported`/согласованный heartbeat contract | Только чтение; проверять реальный heartbeat по существующей HA логике | Предел свежести 300 с по E4; исторический last_updated Packet ID не заменяет live проверку. E2/E4 |
| CO₂ | В E1 registry ни `co2/co_2/carbon_dioxide`, ни mapping для living не найден; E4 `co2: []` | Не подключён в известном контракте; ppm, без demo | Read-only после подключения; пока `-- ppm`/«нет датчика» | Установка планировалась по E4. Физическое наличие не проверено |
| Отопление | `climate.vannaia_komnata_termostat_vannoi_r1_gostinaia_otoplenie`; state heat/off; attrs `current_temperature`, `temperature`, `hvac_action` | Последняя запись heat, current=26.3 °C, target=24 °C, action=idle (10:54:23 МСК) | Существующие `climate.set_temperature` и `climate.set_hvac_mode` подтверждены E1; feedback режим + уставка + action, запрос и питание отдельно | Прямая уставка переводит профиль во «Вручную»; OFF/HEAT синхронизируют профиль. Не обходить профиль/сезон/защиты. E1/E2/E4 |
| Профиль / уставки | `input_select.home_living_profile`: По расписанию / День / Ночь / Вручную / Выключено. `input_number.home_living_day_temperature`, `_night_temperature`, `_manual_temperature`; `sensor.home_living_target_temperature` read-only °C | По расписанию; 24/20/24 °C; target=24 °C. День с `input_datetime.home_living_day_start`=07:00, ночь `_night_start`=23:00 | Согласованный HA adapter должен менять helpers/профиль, затем ждать effective target и climate state. Это ещё не общий Auto heat/cool | HA profile_apply задаёт temperature и heat, либо off по разрешению; расписание остаётся владельцем target. E1/E2 |
| TPI / исполнитель | `sensor.home_living_tpi_request` %; физические `sensor.vannaia_komnata_termostat_vannoi_r1_gostinaia_tpi_zapros_nagreva`, `_pwm_primenennyi`, `_status_otopleniia`; `binary_sensor.vannaia_komnata_termostat_vannoi_r1_gostinaia_tpi_pitanie_privoda` | template request последняя запись 0%; свежесть физических feedback отдельно не проверена | Read-only UI; request ≠ электрическое питание ≠ положение клапана | Существующие min/cycle/P/I helpers `input_number.home_living_tpi_{cycle_minutes,min_on_minutes,min_off_minutes,kp,ki}`: Recorder 30/8/8 мин, 0.35/0.00005. Это действующие настройки, не новый проект. E1/E2/E4 |
| Разрешения / сезон | `binary_sensor.home_living_heating_allowed`; `input_boolean.home_living_cooling_lock`; `input_boolean.home_heating_commissioned`; `input_select.home_heating_season`; `binary_sensor.home_heating_season_active` | allowed=on; cooling_lock=off; commissioned=on; сезон «По датам», active=on (последние записи) | Первоначально read-only; feedback обязан объяснять запрет, а не изображать ON как подачу тепла | allowed требует commissioned, TPI initialized, season, profile≠OFF, валидную room temperature и cooling_lock≠on. E1/E2 |
| Глобальный источник | `select.vannaia_komnata_termostat_vannoi_klimat_upravlenie`; E4 options HA / Ручной / Выключено | Последняя запись HA; live options не прочитаны | Показывать источник. Не переключать глобальный source ради room Manual | Источник влияет на все радиаторы и полы/стену; room Manual не равен аварийному глобальному Ручной. E1/E2/E4 |
| Кондиционер | **HA ID и модель не установлены**. В E1 registry/E2 metadata найдены только 3 radiator climate, AC climate не найден | hvac_modes, supported_features, range/step, fan/swing/preset, availability и feedback неизвестны | Команды AC блокированы до read-only проверки конкретной сущности; нельзя предполагать heat/cool/auto или service | В текущем package найден cooling_lock, но **не найден** выбор heat/cool либо команда кондиционеру. Cooling lock сам по себе не координатор. E1/E2 |

### Существующие защиты отопления

По E4 PI/TPI выполняется на ESPHome; запрет HA, OFF, heartbeat/температура старше 120 с, NaN и превышение уставки на 0.3 °C обнуляют выход и интегратор. После смены источника планировщик начинает с паузы. Электрическое OFF не означает мгновенное закрытие термопривода. Локальные полы/стена сохраняют sensor timeout 45 с, перегрев, гистерезис и минимальные времена. Живые fault states и действующая прошивка в этом срезе не перепроверялись; защита описана по E4, а не объявлена испытанной сегодня.

### Что необходимо добавить для нового UI

**Auto**: одна общая температура, решение heat/cool принадлежит HA. Такого составного HA controller в E1 не обнаружено; существующий profile «По расписанию» управляет отоплением, а не AC. Нужны установленный AC контракт и будущий HA coordinator с явным feedback режима/уставки/блокировки. Deadband, интервалы компрессора, приоритеты и арбитраж не определены этим отчётом.

**Manual**: два независимых UI ON/OFF — отопление и AC. Отопление обязано оставаться в согласованном HA пути с защитами; AC пока unresolved. Нельзя отображать запрос как подтверждённое включение. Нужен арбитраж с profile_apply, чтобы команда не перезаписывалась расписанием и чтобы не допустить несогласованного нагрева/охлаждения. Его политика требует отдельного решения.

**Турбо-проветривание**: только UI таймер и Stop. Никаких команд отоплению, AC, вентиляции, cooling_lock либо автоматике. Это UI addition, а не существующий HVAC режим.

## Погода и обязательный прогноз — только HA

| Slot | Entity / attrs / units | Последний Recorder | Команды / feedback / конфликт |
|---|---|---|---|
| Существующий met, не основной | `weather.forecast_home_assistant`, platform met; state condition; temperature °C, humidity %, pressure hPa, wind_speed km/h, wind_bearing ° | cloudy, 8.2 °C, RH77%, wind7.2; запись 10:22:04 МСК | Только чтение. E1/E2/E4; на отопление не влияет |
| Другие существующие | `weather.yandex_pogoda`, `weather.home_assistant_gismeteo` | cloudy 6.0 °C (10:16:08 МСК); cloudy 7.8 °C (10:44:35 МСК) | Только HA read-only; пользователь выбрал Yandex основным и Gismeteo резервным (уточнение ниже). Не смешивать показатели молча. E1/E2 |
| 3–5 дней, минимум завтра | Forecast array в последних записанных weather attributes отсутствует; daily supported_features/response **не проверены** | Наличие текущей weather entity не подтверждает пригодный daily forecast | Требуется разрешённый read-only HA forecast response/подписка и проверка дат/единиц/availability. До этого явное «прогноз недоступен». Прямой внешний запрос из панели и demo не заменяют HA forecast |

## Ванная — следующий обязательный профиль

| Slot | Entity / attrs / unit / capability | Последний Recorder / availability/freshness | Будущий command / feedback / конфликт / evidence |
|---|---|---|---|
| Воздух ванной | **Не сопоставлен**: отдельная room-air entity не установлена | Availability/freshness неизвестны | Только чтение после физического сопоставления. Нельзя подставлять floor/wall или living. E1/E2 |
| Пол 1 | `sensor.termostat_vannoi_pol_1_temperatura`, °C, measurement | 29.6875 °C, 11:09:11 МСК; live unavailable/fault не прочитаны | Read-only; не называть температурой воздуха. E1/E2 |
| Пол 2 | `sensor.termostat_vannoi_pol_2_temperatura`, °C, measurement | 31.4375 °C, 11:03:40 МСК; возраст изменения сам по себе не freshness датчика | Read-only; физическое соответствие зон ванной/другого помещения требует проверки. E1/E2 |
| Тёплая стена | `sensor.termostat_vannoi_teplaia_stena_temperatura`, °C | 27.25 °C, 11:09:40 МСК | Не подменяет воздух или полотенцесушитель. E1/E2 |
| Полотенцесушитель 1 | **ID не установлен**, capabilities/защита/силовой feedback неизвестны | Не подтверждено | Отдельный будущий +1ч/Stop HA contract; actual relay feedback и deadline/state. Не привязывать к полу/стене по названию. E1/E2 |
| Полотенцесушитель 2 | **ID не установлен**, capabilities/защита/силовой feedback неизвестны | Не подтверждено | Второй независимый +1ч/Stop, собственный deadline/state и actual relay feedback. E1/E2 |
| Таймеры двух приборов | В registry и Recorder metadata не найдены `timer.*`; scripts.yaml пуст; bath timer automation в просмотренных YAML не найдена | **Не существует подтверждённого действующего контракта** | Нужно будущее HA хранение независимых deadline/таймеров и восстановление состояния. Навигация и restart панели не должны сбрасывать таймер. Для HA restart отдельно определить и проверить восстановление/expiry reconciliation |

`switch.sushilka_power` существует, последняя запись off; сопутствуют `sensor.sushilka_current_status`, `_total_time`, `_remaining_time`, `select.sushilka_operation`, delayed_end и notification/error. **Не установлено, что это полотенцесушитель**; характер сущностей допускает другой бытовой прибор. Подключать его к towel slot без подтверждения нельзя. Ни один из двух физических полотенцесушителей этим ID не объявлен.

Существующие `switch.termostat_vannoi_pol_1_avtomatika`, `_pol_2_avtomatika`, `_teplaia_stena_avtomatika` (последние записи on) и time/number helpers — местные термостаты зон с расписаниями, не два независимых полотенцесушителя с продлением часа.

Будущая семантика каждого towel: первое +1ч запускает час; следующее прибавляет ровно час к **оставшемуся** времени; Stop отменяет таймер и запрашивает OFF; expiry запрашивает OFF. Изменение UI только по HA feedback, различать timer active и фактическое питание. Команды +1ч должны сериализоваться/быть атомарными на HA, чтобы повторное нажатие не потерялось; идентификаторы новых helpers/scripts не придуманы. Нужны проверенные независимые нагрузки, их защитная логика и существующие automations до реализации. Неизвестные max duration, deadband и приоритеты не установлены произвольно.

## Готовность

Living temperature/RH, отопление, profile/targets, TPI и глобальный source имеют доказанные ID. **Блокеры реальных команд**: основной свет и override, AC контракт, общий HA Auto heat/cool, два физических towel endpoints и персистентные таймеры; 3–5 daily days пока не доказаны; минимум завтра подтверждён через HA в E5. Следующий этап может использовать эти данные для mock/read-only adapter; подключение реальных действий требует закрыть указанные контракты. `ha-functional-ui-plan.md` не изменялся.


## E5 — уточнение действующего transport и успешный live GET, 11:15–11:16 МСК

После узкой повторной проверки исправлена ошибка выбора порта: `docs/infrastructure/network-map.md` документирует **HTTP/80 и неслушающий TCP/8123**; `current-state-2026-10-20.md` также указывает HTTP80, актуальный workshop runbook — `http://ha.local/`. В текущем `/config/configuration.yaml` нет секции `http:` и явных server_port/ssl/server_host. Конфигурация сама по себе не объясняет transport; порт80 подтверждён **фактическим успешным ответом**, а :8123 не следовало считать стандартным рабочим путём этого дома.

В 11:15:54 МСК выполнены только **GET `http://192.168.0.123/api/states` и GET `/api/services`**, оба успешны, со штатным локально сохранённым HA bearer token. Секрет не выведен/не сохранён в отчёте. Никакого ремонта, restart, config change или service call. Перед изменением этого отчёта сохранена датированная приватная копия в инфраструктурном `local/backups/formapanel-inventory-20261101T…/` (не в Git).

Это уточнение имеет приоритет над ограничениями E3 и историческими таблицами выше:

| Slot | Live evidence / capabilities / availability |
|---|---|
| Living T/RH | `sensor.home_living_temperature`=26.31 °C, RH=48.49%; sample_time обоих 11:15:51 МСК, valid_sources=1, states числовые, не unavailable |
| BLE freshness | `sensor.bthome_sensor_ff38_packet_id`=149, last_reported=11:16:04 МСК. Свежий heartbeat подтверждён; старая запись Recorder не означала stale |
| Heating | Living climate heat, target24 °C, current26.3 °C, hvac_action idle; **hvac_modes=[off,heat], min_temp16, max_temp28, target_temp_step0.1, supported_features385**; last_reported11:15:23. Общий GET services содержит set_temperature/set_hvac_mode/turn_on/turn_off; это наличие domain services, не разрешение любого service для любой entity |
| TPI | Физический request0%, applied PWM0%, energized off, статус «TPI: пауза / ожидание»; numeric/known state, не unavailable. Старый last_reported постоянного выхода не подтверждает свежесть heartbeat; источник и climate доступны |
| Profile / target | По расписанию, target24 °C, day24/night20/manual24. Day/night helpers min16/max28/step0.5; manual min16/max28/step0.1. Все known. Три living automations profile/season, manual-target, mode имеют state on |
| Source / gates | Глобальный source HA, live options HA/Ручной/Выключено; commissioned on, season По датам, season_active on, heating_allowed on, cooling_lock off |
| AC / primary light / timers | Полный live states содержит **только 3 radiator climate**, **2 display-brightness lights**, **0 timer entities**. AC/основной свет и два towel по-прежнему не идентифицированы; наличие иных физических устройств этим не опровергнуто |
| Bath temperatures | Пол1=29.625 °C (last_reported11:12:41), пол2=31.4375 °C (11:14:40), стена27.25 °C (11:12:10); states известны, не unavailable. Это последние сообщения, не самостоятельное доказательство sensor-health; воздух ванной не сопоставлен |
| Candidate dryer | `switch.sushilka_power` live off; связь с любым towel не установлена |
| Weather | met current8.2 °C, supported_features3; gismeteo current7.8 °C, supported_features3; Yandex current6 °C, supported_features6. Все cloudy, known state. Текущие значения и forecast freshness следует отображать раздельно |

### Прогноз на завтра действительно доступен через HA GET

`weather.yandex_pogoda` возвращает в live state attributes **forecast_hourly** до `2026-11-02T23:00:00+03:00` и **forecast_twice_daily**, включая:

- `2026-11-02T00:00:00+03:00`, is_daytime=false, native_temperature6, native_templow5, condition cloudy;
- `2026-11-02T12:00:00+03:00`, is_daytime=true, native_temperature7, native_templow5, condition rainy.

У weather temperature_unit=°C. Это данные существующего HA integration, без внешнего запроса из панели, без вызова action. Минимальный forecast slot **«завтра» подтверждён**; UI adapter может использовать эти HA attributes после проверки native-unit mapping. Forecast last_updated/last_reported источника — 10:16:08 МСК. **3–5 дневных суток не подтверждены**. GET `/api/services` подтверждает `weather.get_forecasts`, но action/response не вызывался; met/gismeteo daily response остаются непроверенными. Нельзя объявить сервис недоступным лишь потому, что Recorder не сохраняет forecast attributes.

Итог актуального среза: read-only HA путь работоспособен, living sensors/heating/source и минимум прогноза «завтра» имеют live evidence. Блокеры действий по свету, AC, двум towel и новой HA координации/таймерам сохраняются.


## E6 — решения владельца и проверка weather registry, 11:16–11:17 МСК

**Погода выбрана владельцем:** основная `weather.yandex_pogoda`, резерв `weather.home_assistant_gismeteo`; met не основной. Повторное read-only чтение текущих registry подтверждает:

| Назначение | Entity | Device ID | Config entry ID | Entity area / device area |
|---|---|---|---|---|
| Основной | `weather.yandex_pogoda` | `5b21c4c47159648ae445a0e92747c8a2` | `01M2KHM4952FE1PDN3V434GBM0` | null / null; area не назначена |
| Резерв | `weather.home_assistant_gismeteo` | `fd37f251caf49fbb50dba19adaceb05c` | `01M2MV9AEVZ7NGA24YK29E9R2F` | null / null; area не назначена |

Отсутствие HA area у weather не означает отсутствие источника: это общедомовая погода. Минимум «завтра» у выбранного основного источника уже доказан E5. Правила freshness/fallback и явное отображение выбранного источника нужно оформить в adapter; не смешивать измерения источников.

**Климатический command contract изменён владельцем:** панель работает **только через будущие виртуальные HA сущности room mode / room target / manual heat / manual AC**. Реальные ID этих новых сущностей ещё не установлены. Все перечисленные выше существующие device services служат доказательством текущего устройства HA и входами будущего coordinator, **не являются допустимыми прямыми действиями панели**. HA coordinator работает независимо от панели, сохраняет арбитраж, защиты и владение автоматикой; restart/отключение панели не должен останавливать управление климатом.

Каждой панели требуется явно заданная room identity и allowlist только её контекста. Living panel не получает команды bedroom/office/bath либо глобального источника; глобальный source в отчёте — read-only диагностический факт. Room Manual не переключает глобальный ESPHome source. Auto имеет одну room target, HA выбирает heat/cool; Manual имеет виртуальные отдельные heat/AC ON/OFF, а не команды физическим устройствам. Новые виртуальные ID/координатор в этом срезе не созданы. Turbo по-прежнему только UI timer/Stop, без HVAC действий.

Итог после решений владельца: source погоды больше не unresolved; living read-only данные и forecast завтра готовы к контракту. Для климата необходимы **виртуальный room contract и независимый HA coordinator**, а также фактический AC endpoint за ним; для света и двух towel остаются идентификация нагрузок/автоматики и независимые персистентные таймеры. Перед этим дополнением вновь сохранён датированный приватный backup только отчёта.
