# FormaPanel: инструкция реализации HA UI

**02.11.2026: HA-интеграция активирована.** Абстракции гостиной, реальные T/RH и пятидневная погода работают; действующий климат сохранён. [Проверки и текущий статус разрешения панели/OTA](../06-validation/ha-living-integration-2026-11-02.md).


**Текущее состояние 02.11.2026:** утверждённый дизайн гостиной реализован в LVGL; 12 native кадров и factory/OTA BIN проверены. [Результат, preview и оставшиеся этапы](../06-validation/functional-living-implementation-2026-11-02.md). HA package остаётся неактивированным candidate; устройство не прошивалось. Исторический visual gate ниже пройден, следующий — одна пилотная панель living.


**Актуально: visual approval получен 01.11.2026.** Владелец утвердил макеты и разрешил реализацию с субагентами; единственная правка — отражённая левая полудуга Climate с центром (480,240). Предыдущая остановка на visual gate ниже сохранена как история и больше не действует. Все остальные границы HA/OTA сохраняются.


**Исторический visual gate (пройден):** визуальные макеты →
доработка/утверждение → логика. Все последующие инструкции реализации читаются
с этим приоритетом. Начатая логика не развивается до visual approval.
См. [ревью 01](../03-design/functional-visual-review-01.md): фон RH-01 50%,
полудуга Climate у края экрана, пиктограммы ON/OFF вместо switch-плашек.
Новые макеты существуют отдельно от runtime; состояние прежних технических
работ и ограничений записано в конце документа ревью.

Дата: **01.11.2026**, время/даты приёмки — Europe/Moscow.
Статус: **living runtime и сборка готовы; live HA/pilot acceptance остаются**.
Основание: [решения и основной план](ha-functional-ui-plan.md), уточнения владельца,
переданные в этот диалог 01.11.2026. Этот документ детализирует исполнение, не
заменяет решения владельца и не объявляет новые HA возможности существующими.

## 1. Утверждённый результат и пределы полномочий

1. Первая вертикаль — **living, одна физическая панель**. Затем обязательна
   ванная; прихожая, спальня, кабинет и тиражирование — последующие этапы.
2. Пять основных страниц: главная, Свет, Климат, Погода, Настройки/Информация;
   дочерний экран `turbo_ventilation` открывается из Климат, Back возвращает туда.
   Погода и весь климатический блок главной открывают соответствующие страницы.
   Home/Back явные, настройки доступны со вторичных страниц. Часы показывают время.
3. Одно короткое касание лампы запрашивает **одно переключение основного света**
   и **сразу** открывает Свет. Переход не ждёт результата HA и работает при
   недоступном свете/HA. Загрузка страницы и входящие состояния команд не создают.
   Старое предложение A/B больше не используется.
4. Климат Auto — одна заданная температура; выбор отопления/охлаждения делает HA.
   Manual — отдельные включение/выключение «Отопление» и «Кондиционер».
   Панель изменяет **виртуальные комнатные сущности HA**, а не реальные HVAC
   устройства. Логика HA независима от панели. Это целевое поведение, не
   доказательство наличия готового HA Auto-контроллера.
5. «Турбо-проветривание» — **только UI-заглушка** с таймером, обратным отсчётом
   и принудительным Стоп. Ни запуск, ни Stop, ни expiry не посылают HVAC команд,
   не приостанавливают действующее отопление, кондиционер или вентиляцию.
6. Погода — текущие детали **и прогноз** на 3–5 дней либо минимум на завтра.
   Основной источник — **Яндекс.Погода**, резервный — **Gismeteo**, оба через HA.
   Отсутствующие прогноз/датчик/атрибут не заменяются demo числами.
7. Ванная — собственная главная, температура воздуха и пола, **два независимых**
   полотенцесушителя: +1ч, СТОП, остаток времени у каждого. Первое +1ч задаёт час,
   последующие добавляют час к остатку; Stop отменяет свой таймер и запрашивает
   выключение своего прибора. Надёжностью и сроком выключения владеет HA.
8. Проверенная композиция RH-01, фон и графика сохраняются. **Выбран вариант 2 —
   Comfortaa**: крупные цифры и погода Bold 700, малый климатический текст Medium
   500. Шрифт выбран окончательно; перенос в source и LVGL проверка ещё предстоят.
9. Каждая панель знает свою комнату: постоянные `panel_id`, `room_id` и
   подтверждённый HA `area_id`; контекстные свет/климат разрешены только для неё.

Сравнение шрифтов уже подготовлено в
[отдельном документе](../03-design/rh01-font-comparison-2026-11-01.md):
реальные TTF, одинаковая геометрия, предварительный browser render.
Владелец выбрал правый вариант Comfortaa. Browser render не заменяет будущую
firmware/device проверку.

Сейчас разрешены подробное планирование, read-only инвентаризация и работа
субагентов. Этот документ не является разрешением изменять живой TPI,
включать бытовые нагрузки, перезапускать контроллеры или выполнять OTA.
Перед изменением действующей системы применяются
[правила работы](../../../../instructions/agent-work-rules.md): проверить фактический
узел/путь, сохранить датированный backup, объяснить изменение/откат, проверить
синтаксис, затем результат. Не задавать заново уже решённые вопросы из списка выше.

## 2. Фактическая основа и источники

| Область | Подтверждённая основа | Что этим не подтверждено |
|---|---|---|
| Визуальный прототип | Владелец испытал его на железе и принял внешний вид | Точный SHA/BIN, память, reconnect, все touch/HA сценарии |
| Исходники | `D:\Work\Projects\Home\panels\FormaPanel`; много изменённых и untracked файлов | Что весь рабочий набор сохранён в Git remote |
| HA source | `/config/esphome/formapanel-rh01`; worker видит тот же checkout как `/homeassistant/esphome/formapanel-rh01` | Совпадение Windows working tree с HA перед новой правкой |
| Сборка | Workshop 0.1.1; ESPHome 2026.10.1, LVGL 9.5.0, ESP-IDF 5.5.6 по действующему runbook | Успех будущих config/native/firmware заданий |
| UI | Общие `rh01-ui.yaml`, `info-page.yaml`; living/bedroom profiles | Реальные бытовые subscriptions/actions и новые пять страниц |
| Климат | Существующий HA профиль/сезон/уставки и локальный ESPHome TPI | Единый Auto heat/cool, готовый Manual для AC |

Перед реализацией перечитать [development](../development.md),
[компоновку](../04-architecture/source-composition.md),
[методологию](../02-research/effective-ui-development-2026-11.md),
[runbook](../06-validation/build-and-preview-runbook.md),
[инфраструктуру](../../../../docs/infrastructure/ha-formapanel-workshop.md),
[климат](../../../../climate/README.md).
Прежние screens/rooms содержат предложения, включая дату и старые жесты;
они не отменяют новые решения.

### 2.1. Контракт инвентаризации

Отдельный отчёт инвентаризации должен содержать источник каждого значения:
**live API**, **актуальный файл HA**, **registry**, **история Recorder** или
**локальная копия**. Registry доказывает регистрацию, не доступность/работу.
История не доказывает текущий state. Ошибка live API не означает отсутствие устройства.
Не сохранять токены, ключи, cookies или полные секретные конфиги в отчёте.

Для каждого slot фиксировать: entity ID, domain, атрибут, тип, единицу,
допустимый диапазон/шаг, capabilities, room/device, freshness, availability,
источник и время проверки; для команды — service/script, аргументы, семантику
автоматики, ожидаемый state и timeout. Непроверенный binding блокирует соответствующую
live-команду, но не разработку mock UI.

| Slot | Нужное доказательство перед live-включением |
|---|---|
| `living.light.primary` | Реальный исполнитель/группа; ручное действие; все automation/scripts, способные вернуть свет обратно |
| `living.light.items[]` | Реальные группы, brightness/color_temp capabilities, диапазоны и подтверждение |
| `living.air.temperature/humidity` | BTHome источник, единицы, Packet ID freshness и производные HA сущности |
| `living.air.co2` | Установлен ли датчик, валидное измерение; отсутствие — отдельное состояние |
| `weather.current` | Реальный weather entity, condition, temperature, wind, единицы и дата обновления |
| `weather.daily[]` | Источник daily forecast в HA, даты, min/max/condition, горизонт минимум завтра |
| `living.hvac.heat` | Действующая уставка/профиль/разрешение/TPI, запрос и фактическое питание, защиты |
| `living.hvac.cool` | AC entity, режимы, температура/шаг, min cycle, наблюдаемое состояние/доступность |
| `living.hvac.coordinator` | Существует ли HA heat/cool coordinator; если нет — отдельная новая реализация |
| `bathroom.air/floor` | Раздельные физические источники; несколько зон пола не объединять без решения |
| `bathroom.towel[1/2]` | Два разных канала, каждый исполнитель и feedback; существующие таймеры/automation и ограничения |

### 2.2. Полученные факты: текущий контракт, не demo

Полная таблица и методы получения — в
[HA inventory](ha-functional-ui-inventory-2026-11-01.md). Итоговый приоритет —
live E5/E6 **01.11.2026 11:15–11:17 МСК**, поверх прежних Recorder E2.
Документированный HA HTTP endpoint использует порт **80**, не 8123. Read-only
GET states/services успешны; ничего ремонтировать не потребовалось. Повторять
доступ через действующий приватный механизм, не копировать токен в код/отчёт.

| Slot | Подтверждённый ID / свойства | Что делать дальше |
|---|---|---|
| Room T/RH | `sensor.home_living_temperature`, `sensor.home_living_humidity`; `sample_time`, `valid_sources`; 26.31 °C / 48.49% в срезе | Подписка и quality; эти числа не использовать как live defaults |
| BLE heartbeat | `sensor.bthome_sensor_ff38_packet_id`, свежий live last_reported | Использовать действующую HA freshness, не Recorder last_changed |
| Existing heating | `climate.vannaia_komnata_termostat_vannoi_r1_gostinaia_otoplenie`; modes off/heat; min16/max28/step0.1; heat/idle, target24 в срезе | Панель только читает; будущий HA coordinator единственный пишет сюда |
| Existing profile | `input_select.home_living_profile`: По расписанию / День / Ночь / Вручную / Выключено | Не считать этим новым Auto/Manual; согласовать ownership с profile_apply |
| Existing target | `sensor.home_living_target_temperature`; `input_number.home_living_day_temperature`, `input_number.home_living_night_temperature`, `input_number.home_living_manual_temperature` | Existing day/night шаг0.5, manual0.1; новый virtual target проверить с AC range |
| Gates | `binary_sensor.home_living_heating_allowed`, `input_boolean.home_living_cooling_lock`; global `select.vannaia_komnata_termostat_vannoi_klimat_upravlenie` | Read-only диагностика; никаких panel writes в общий источник/season/TPI |
| CO₂ | Нет сопоставленного источника | Явное отсутствие, не `680 ppm` из prototype |
| Main light / AC | Не сопоставлены; live обнаружены только 2 display lights и 3 radiator climates | Нужна идентификация устройств/интеграций и ручной автоматики; не угадывать |
| Yandex primary | `weather.yandex_pogoda`; registry совпал с device/config ID владельца; `forecast_hourly`, `forecast_twice_daily` содержат завтра | Реализовать нормализацию; есть минимум завтра, 3–5 суток ещё не доказаны |
| Gismeteo backup | `weather.home_assistant_gismeteo`; device совпал; текущая погода доступна, forecast response ещё не прочитан | Проверить backup forecast, TTL и failover на fixtures/HA |
| Floor sensors | `sensor.termostat_vannoi_pol_1_temperatura`, `sensor.termostat_vannoi_pol_2_temperatura` | Числовые live состояния есть; выбрать физическую зону ванной; не подменять воздух |
| Bathroom air / towels | Воздух и два прибора не сопоставлены, live timer entities нет | Инвентаризация endpoints/защиты, затем persistent HA contracts |

`switch.sushilka_power` не подтверждён как полотенцесушитель; не использовать
его по похожему имени. Реальный `area_id` living/панели пока не записан в
контракт: закрыть при provisioning. Weather registry area=null у обоих источников
допустимо, это общедомовая погода. Отсутствие AC/light в срезе не доказывает,
что физического устройства нет или невозможно подключить его позже.

Что ещё нужно выяснить до команд: (1) точный основной свет и конфликт автоматики;
(2) AC интеграцию/режимы/минимумы; (3) virtual room contract и HA coordinator;
(4) физические bathroom air/floor/towel mappings; (5) persistent timer/off recovery.
Forecast завтра больше не блокер наличия источника, но adapter/render/fallback и
device приёмка ещё впереди. Эти неизвестные не возвращают закрытые NAV/room/Auto
решения на повторное согласование.

## 3. Владение состоянием и запреты

HA — источник бытового состояния, уставок, разрешений и таймеров полотенцесушителей.
Контроллер сохраняет существующие TPI, минимумы и температурные защиты.
Панель — отображение/ввод; она не вычисляет PI/PID, сезон или PWM и не пишет
глобальный «Климат — управление». Никаких изменений TPI других комнат.

Локально панель владеет только навигацией, pending-индикаторами, настройкой
своей подсветки и демонстрационным turbo-таймером. UI countdown бытового таймера
вычисляется из HA deadline; экран не отвечает за выключение реле.

Каждое входящее значение проходит нормализацию → state reducer → render.
Каждое пользовательское действие проходит intent → capability/availability guard →
adapter → ожидание подтверждённого входа. Render не вызывает intent/HA action.
Mock и HA адаптеры имеют одинаковые script/state контракты, но никогда не
подключаются одновременно в один target.

### 3.1. Комнатный контекст

`panel_id` идентифицирует физическую панель, `room_id` — стабильный ключ профиля
(`living` первым), `area_id` — фактический ID пространства HA. Название комнаты
для человека может меняться без смены bindings. При вводе в эксплуатацию
сопоставить panel/device → room → HA area → разрешённые virtual entities и light
endpoint. Реальный area ID не угадывать по слову living; получить из registry.

Общий UI вызывает `light_primary_toggle`/`room_target_set` без выбора чужого
entity ID. Adapter берёт endpoints только из собственного проверенного room
contract. HA room scripts имеют фиксированные targets/allowlist, не принимают
произвольный entity ID от панели. При несовпадении room/area, пустом binding или
неизвестной версии контракта контекстные команды disabled; данные и диагностика
объясняют причину. Перенос панели в другую комнату требует явного перепривязывания,
никакого определения комнаты по SSID, weather location или совпадению имени.

HA Area — организационная группировка, **не механизм авторизации**. Не отправлять
широкое `light.toggle` на всю area: там могут быть дисплей/backlight и другие
нагрузки. Для основного света использовать явный room endpoint. Общий контроллер
отопления физически расположен в ванной, но его living сущность относится к
гостиной: использовать entity-level mapping и проверенный semantic slot, а не
только area общего физического устройства. Weather и diagnostics не являются
контекстным управлением нагрузками.

Основание подхода: официальные HA [Areas](https://www.home-assistant.io/docs/organizing/areas/)
группируют устройства/сущности по помещениям. Наши явные bindings/allowlist
добавляют проектную защиту от ошибочного обращения к другой комнате; без отдельной
системы прав они не объявляются криптографической изоляцией скомпрометированной панели.

## 4. Планируемое дерево исходников

Обозначения: **E** — существует; **N** — предстоит создать; **M** — точечно изменить.
Имена новых файлов/IDs ниже — проектные, не утверждение их существования.

```text
firmware/esphome/
  boards/guition-s3-480.yaml                 E  hardware, без UI/HA логики
  packages/connection.yaml                  E  сеть/API/OTA, секреты отдельно
  packages/diagnostics.yaml                 E  диагностика панели
  packages/rh01-ui.yaml                     M  совместимый legacy facade
  packages/info-page.yaml                   E  legacy demo info для прежних entry
  packages/ui/resources.yaml                N  общие images/fonts с прежними ID
  packages/ui/runtime.yaml                  N  panel_ui/display/touch, общие стили
  packages/ui/pages/room-home.yaml          N  прежняя RH01 геометрия без commands
  packages/ui/pages/lighting.yaml           N  capabilities/список света/feedback
  packages/ui/pages/climate.yaml            N  Auto/Manual + turbo-заглушка
  packages/ui/pages/turbo.yaml              N  дочерний экран таймера-заглушки
  packages/ui/pages/weather.yaml            N  current + daily forecast
  packages/ui/pages/system.yaml             N  яркость/связь/версия/freshness
  packages/ui/pages/bathroom-home.yaml       N  отдельная геометрия ванной, два towel
  packages/ui/navigation.yaml               N  Home/Back, bounded history, route IDs
  packages/ui/events.yaml                   N  touch -> intents; без прямых services
  packages/ui/state.yaml                    N  входы/reducer/render/command status
  packages/ui/turbo-demo.yaml               N  исключительно локальный таймер
  packages/behavior/legacy-demo.yaml         N  прежний lamp toggle только для legacy
  packages/behavior/mock.yaml               N  те же intent IDs, детерминированные входы
  packages/behavior/ha.yaml                  N  transport/доступность/общий adapter
  packages/behavior/ha-lighting.yaml         N  verified light subscriptions/actions
  packages/behavior/ha-climate.yaml          N  verified HVAC subscriptions/intents
  packages/behavior/ha-weather.yaml          N  HA weather bridge subscriptions
  packages/behavior/ha-towels.yaml           N  два независимых persistent HA timers
  profiles/rh01-shared.yaml                  E  legacy composition, bedroom demo
  profiles/residential-ui.yaml              N  один набор общих жилых страниц
  profiles/bathroom-ui.yaml                 N  bathroom home + общие страницы
  profiles/living.yaml                      M  новая общая room UI composition
  profiles/bedroom.yaml                     E  legacy, до отдельного тиражирования
  profiles/bathroom.yaml                    N  обязательный второй этап
  bindings/living.yaml                      N  только подтверждённые entity IDs/параметры
  bindings/bathroom.yaml                    N  свои entities, floor/towels
  targets/living.yaml                       M  board + connection + UI + HA adapter
  targets/bathroom.yaml                     N  отдельное device name и свои bindings
  previews/living.yaml                      M  те же UI/capabilities + mock
  previews/bathroom.yaml                    N  та же bathroom UI + mock
  previews/functional-backend.yaml          N  host/display/capture runtime
  previews/scenarios/living.yaml            N  последовательность fixtures и PNG
  previews/scenarios/bathroom.yaml          N  оба таймера и ошибки/восстановление
  previews/room-backend.yaml                E  legacy bedroom on/off/info
  previews/host-rh01.yaml                   E  контроль неизменности RH01
  components/ui_contract/                  N* маленький shared C++ reducer, если нужен
config/ha/contracts/living.yaml             N  machine-readable verified slot contract
config/ha/contracts/bathroom.yaml            N  timers/capabilities/freshness
config/ha/panels.yaml                        N  panel/room/area и allowlisted endpoints
config/ha/packages/formapanel-weather.yaml   N* HA forecast bridge при необходимости
config/ha/packages/formapanel-living.yaml    N* coordinator/intent endpoints при отсутствии
config/ha/packages/formapanel-bathroom.yaml  N* HA timers/scripts/recovery
config/workbench-targets.json               M  living label; bathroom entries позже
tests/test_ui_contracts.py                  N  schema/isolated adapter/bindings checks
tests/test_ui_state.cpp                     N* реальные reducer transitions, не копия
tests/test_ha_contracts.py                   N  command/restore/forecast fixtures
docs/06-validation/ha-functional-ui-*.md     N  фактические отчёты этапов
```

`N*` создавать только если необходим соответствующий компонент. Если reducer
вынесен в C++, host и device обязаны использовать один код; тесты не переписывают
его алгоритм на Python. Не создавать local ESPHome component лишь ради папки.
HA package candidates — проверяемые исходники, не автоматически установленная
интеграция. Их окончательный путь подключения определить по реальному HA config.
Большую UI-композицию не копировать по комнатам. Повторяющиеся карточки получают
стабильные ID через include variables, не runtime entities из произвольного текста.

### 4.1. Совместимость и переход без дрейфа

Сохранить `panel_display`, `panel_touch`, `panel_ui`, `rh01_home`,
`rh01_lamp_button`, `rh01_lamp_image`, `rh01_lamp_on/off` и существующие label IDs.
Для functional system использовать `panel_system`; legacy `panel_info` оставить
у прежнего demo. Room home route разрешается через профиль, поэтому ванной
не нужен фиктивный второй `rh01_home`. Новый capture backend не зависит от legacy info.

Сначала вынести resources с неизменными bytes/параметрами. Затем runtime/layout.
Старый `rh01-ui.yaml` становится facade, включающим shared layout и legacy behavior;
новый living подключает shared layout напрямую, **без** legacy behavior/info patch.
Так старый `on_value`/`on_long_press` не попадёт в live entry через merge.
Не добавлять новые обработчики поверх существующих в надежде на overwrite:
`!extend` сливает элементы. Если промежуточная миграция использует patch, удаление
старых ключей через `!remove` проверять в итоговой config.

У нынешней лампы `checkable: true`, локальный `on_value`, а `info-page.yaml`
добавляет `on_long_press`. У functional лампы checkable отключён; одна точка
`on_short_click` вызывает composite intent. Никаких commands в `on_value`,
`on_boot`, page show, reconnect или render. Удержание не вызывает вторую команду.
Программные updates LVGL также способны вызывать update events; guard render
должен защищать весь путь, а не один конкретный slider.
Проверено по исходникам pinned ESPHome 2026.10.1:
[trigger.py](https://github.com/esphome/esphome/blob/2026.10.1/esphome/components/lvgl/trigger.py)
(`on_value` подписан также на UPDATE_EVENT) и
[automation.py](https://github.com/esphome/esphome/blob/2026.10.1/esphome/components/lvgl/automation.py)
(программный update value может его отправлять).

## 5. State/command/navigation contracts

### 5.1. Входное состояние

Для slot хранить `configured`, `supported`, `valid`, `availability_reason`,
typed `value`, unit, `received_at_monotonic`, source timestamp при наличии,
`revision` и connection epoch. Время устройства может быть ещё не синхронизировано:
локальные timeout измеряются монотонно, реальные HA deadline требуют валидных часов.

Различать: `not_configured` (например CO₂ ещё нет), `unknown` (ждём первый state),
`unavailable` (источник недоступен), `stale` (свежесть потеряна), `valid`,
`unsupported` (нет capability). Старое число допустимо только с явной отметкой
возраста/недоступности; на главной по умолчанию `--`, детали объясняют причину.
Не делать вывод о свежести BLE по изменению температуры: использовать существующий
Packet ID/freshness. Не объявлять стабильное on/off света stale только потому,
что оно долго не меняется; контролировать связь и availability источника.

Связь API с каким-либо клиентом ещё не доказывает свежую подписку HA. Reconnect
создаёт новый epoch: до первого валидного snapshot управляющие actions disabled.
Demo substitutions присутствуют только в legacy/mock entry, не в live defaults.

### 5.2. Команда

`Command = {local_id, slot, operation, requested_value, pre_revision,
pre_value, started_monotonic, deadline, status}`. Статусы: idle, pending,
confirmed, rejected, timed_out, unavailable. Локальный ID не выдаётся за HA
correlation ID, если transport его не возвращает.

1. Проверить binding/capability/current state/connection и незанятый command slot.
   Исключения: towel increment принимает разные уникальные события, Stop имеет
   приоритет над pending своего канала; подробный контракт в §9.
2. Зафиксировать ожидаемый результат **до** отправки, чтобы не пропустить быстрый ответ.
3. Отправить ровно один intent. Успех service call означает только принятие запроса.
4. Входящий новый валидный state нужного slot сравнить с expected predicate.
   Совпадение предшествующего cached state не подтверждает новую команду.
5. Ошибка/timeout не изменяет confirmed value и не запускает автоматический retry.
   Поздний state обновляет отображение, но не переписывает историю как своевременный успех.
6. При потере HA pending завершается состоянием неопределённости; после reconnect
   сверить snapshot, не переотправлять command. Exactly-once через разрыв связи не обещать.

Для света expected — противоположное подтверждённому состоянию на момент нажатия,
если реальная семантика endpoint именно toggle. Script/scene может требовать другого
feedback predicate, заданного инвентаризацией. State convergence не доказывает,
что изменение вызвала именно панель: внешняя автоматика может действовать одновременно.
Повторные taps по тому же slot во время pending не ставить в очередь и не повторять
toggle; дать доступный текст «Ожидание». Состояние pending отдельно от confirmed on/off.

Начальные **параметры для mock/приёмки**, не измеренная характеристика сети:
light command timeout 5 с, coordinator/helper state 10 с. После наблюдений уточнить
по slot. Включение компрессора/реальный нагрев имеют свои задержки и не должны
проваливать подтверждение принятого режима; intent accepted и actuator active — разные поля.
Слайдер отправляет одно итоговое значение на release, −/+ объединяют быструю серию
в последний setpoint; внешнее HA update не порождает обратный запрос.

### 5.3. Навигация

Routes: `home`, `lighting`, `climate`, `weather`, `system` и дочерний
`turbo_ventilation`; `home` выбирает профиль, Back из turbo ведёт в Climate.
История ограничена 8 переходами, повтор текущей страницы ничего не добавляет.
Home очищает историю; Back извлекает предыдущую, пустая история ведёт Home.
System из Climate → Back возвращает Climate. Page show — только render/route state.

Composite `light_primary_tap`: синхронно принять intent/поставить pending или
причину отказа, открыть Lighting в том же обработчике, выполнить неблокирующую
отправку. Не ждать HA action response перед page show. При offline первая часть
не отправляет запрос, вторая всё равно открывает страницу. Сначала блокировать
повторный ввод, затем отправлять — это устраняет гонку быстрых повторов.

Состояния команд, turbo и бытовых таймеров живут вне страницы. Смена страницы
не отменяет и не повторяет их. На boot только Home/restore subscriptions;
никаких автоматических бытовых команд из панели.

## 6. Подробные страницы и данные

| Страница | Содержание и поведение | Условия доступности |
|---|---|---|
| Главная | Те же фон/позиции/графика, живое HH:MM, погода/ветер, T/RH/CO₂, confirmed lamp icon; невидимые hit areas | Без первой синхронизации `--:--`/`--`; нет даты/секунд/новой постоянной панели навигации |
| Свет | Основной свет, существующие группы; confirmed/pending/error; brightness/temperature только если поддерживаются | Нет HA/первого state — действия disabled, Home/Back работают |
| Климат | Auto/Manual, единая Auto уставка; Manual heat/AC отдельные controls, фактическая активность и причина запрета; переход в turbo | Неподключённый coordinator/AC показан честно; не имитировать Auto локальным toggle |
| Turbo | Дочерний экран с явной подписью «Заглушка», длительностью, countdown и Stop | Никаких реальных commands; Back → Climate |
| Погода | Current condition/T/wind/details, daily cards с датой/минимумом/максимумом/condition; прокрутка при необходимости | Отсутствующие поля `--`, прогноз недоступен явно; нет подставленных sunny/zero |
| System | Профиль/версия/source, HA connection, freshness, подсветка панели | Не добавлять reboot/network editing/service controls без отдельного согласования |
| Ванная | Собственный home, T воздуха и пола; два towel с собственными +1ч/Stop/remaining/state | Каждый channel независимо available/pending; проблема одного не отключает второй |

Шрифты: сначала воспроизводимый исторический baseline Nunito для проверки
чистого extraction; затем отдельным шагом перенести **выбранный Comfortaa**
с лицензией, подтвердить реальные Cyrillic/°/%/CO₂/minus glyphs
и крайние строки. Замена семейства не должна молча сдвигать остальные элементы.
Все строки/отрицательные температуры/высокий CO₂ проверять на clipping.
Погодная condition icon обязана соответствовать данным: существующая одна картинка
не является набором для всех условий. Неизвестная condition — нейтральное состояние,
при необходимости добавить согласованный комплект в прежнем графическом стиле.

Входы для font migration уже локально в `reports/local/font-comparison/`:
`Comfortaa-Variable.ttf`, `Comfortaa-Bold.ttf`, `Comfortaa-Medium.ttf`,
`Comfortaa-OFL.txt`, `provenance.json`. Официальный Google Fonts blob
`8b8e5f81bf740a8154bb6cd9f4eee5ac4bda6b18` указан в design report. После backup
добавить постоянный `assets/source/fonts/comfortaa/` с TTF, своей OFL и metadata;
не перезаписывать Nunito OFL/manifest. Проверить хеши input, лицензию, веса700/500,
размеры72/64/30/21 и те же home координаты. Runtime не ссылается на reports/local.
Legacy эталон Nunito сохраняет свой baseline; functional living получает Comfortaa
через font substitutions/resources без копирования home geometry. Новый native
Comfortaa baseline принимается отдельно от побитной проверки legacy extraction.

## 7. Климат Auto/Manual: контракт до реализации

### 7.0. Обязательный виртуальный интерфейс HA

Уточнение владельца: все климатические виджеты изменяют виртуальные сущности
комнаты. Это применимый штатный подход: HA
[input_select](https://www.home-assistant.io/integrations/input_select/) хранит
режим, [input_number](https://www.home-assistant.io/integrations/input_number/)
— числовую уставку; их изменения могут запускать автоматику. Предлагаемая
реализация ниже — проектный выбор, не утверждение, что HA требует именно её.

| Виртуальный slot | Планируемый тип | Панель пишет | HA возвращает |
|---|---|---|---|
| `room.hvac.mode` | input_select / существующий virtual select | Auto или Manual | Подтверждённый режим и revision |
| `room.hvac.target` | input_number / существующий virtual number | Одну целевую T в допустимом диапазоне/шаге | Сохранённую и effective уставки |
| `room.hvac.manual_heat` | input_boolean / virtual switch | Запрос heating ON/OFF | Desired, accepted/blocked и actual heating отдельно |
| `room.hvac.manual_cool` | input_boolean / virtual switch | Запрос AC ON/OFF | Desired, accepted/blocked и actual cooling отдельно |
| `room.hvac.status` | HA read model sensors/attributes | Ничего | branch/reason/availability/actual/last applied revision |

Это slot имена, не придуманные действующие entity IDs. После inventory выбрать
существующие подходящие helpers либо создать новые в HA candidate package с
проверкой коллизий. Не переиспользовать нынешний profile helper как Auto/Manual
простым переименованием. Device `climate.*`, физические switches, TPI и global
source не являются write targets панели. Panel action allowlist допускает только
собственные virtual helpers или room script, атомарно изменяющий эти helpers.
HA coordinator единственный превращает virtual intent в реальные HVAC actions.

Принятие helper state — подтверждение сохранённого желания, **не включения
устройства**. UI показывает applied/blocked/actual по coordinator/actuator
feedback; requested ON при protection OFF не рисуется как фактический нагрев.
Режим и уставку при одновременной правке менять атомарным room intent либо
исполнять по явной версии, чтобы промежуточный snapshot не запускал старый режим.
Режим/target сохраняются HA; при загрузке панели нет записи defaults поверх них.
Coordinator на startup и изменении входов сверяет desired/actual и защиты,
а не зависит только от события с панели. Отключённая или заменённая панель не
останавливает климат. Другой HA dashboard использует те же virtual entities.

Обязательные tests: панель offline при работающем HA → control продолжает работу;
перезагрузка панели → 0 HVAC writes/default resets; изменение virtual helper из
HA → тот же путь исполнения; неподходящий room contract → 0 чужих actions;
в generated panel config отсутствуют прямые writes в физический HVAC.

### 7.1. Что сохраняется

Существующая система: HA владеет профилями «По расписанию / Вручную / Выключено»,
уставками, сезоном; ESPHome исполняет TPI. Это **другая ось**, чем новый UI Auto/Manual.
Не отображать существующее «По расписанию» словом Auto без heat/cool coordination.
Изменение температуры на прежней HA карточке переводит профиль в «Вручную»;
изменение уставки в OFF сохраняет её без включения. Сохраняются действующие
temperature/heartbeat timeout, сезон/разрешения, минимумы TPI, отсутствие второго PID.

### 7.2. Действия HA coordinator

Предпочесть существующий проверенный coordinator, если он обнаружится.
Иначе подготовить отдельный, узко ограниченный living HA package и сначала
испытать его на helpers. Он выбирает режим, а не рассчитывает PID:

```text
input: mode, target, actual_temperature + freshness,
       heat/cool capability + availability, existing permits/protections,
       actual actuator state, device minimum-cycle constraints
output: requested branch NONE/HEAT/COOL + status/reason
execution: only verified living endpoints, existing TPI/AC regulate output
```

Auto: при валидном источнике сравнивать T с согласованными порогами вокруг target.
Гистерезис входа/выхода должен разделять HEAT / IDLE / COOL; переход между
противоположными ветвями выполняется через выключение, подтверждение и требуемую
минимальную паузу. Запрет сезона/защиты отображается, а не обходится.
Если одна ветвь недоступна, не выдавать полную работоспособность Auto; HA сообщает
degraded/blocked и допустимую ветвь по принятой политике. При потере датчика
не продолжать принимать решения по старой температуре.

**До установки coordinator заполнить таблицу**, опираясь на устройства и текущую
HA автоматику; значения не выдумывать:

| Решение | Источник/правило выбора | Блокирует |
|---|---|---|
| Целевая единая уставка, min/max/step | Пересечение поддерживаемых диапазонов, шагов и комнатных ограничений | Live Auto setpoint |
| Владелец уставки и связь с расписанием | Текущие HA профили; отдельное явное описание, кто может перезаписать target | Coordinator deployment |
| Heat/cool enter/exit deadband | Спецификации/существующий coordinator/наблюдения; утвердить конкретные значения | Live Auto |
| Min-on/min-off AC, смена heat/cool | Спецификация реального AC и existing automation; не заменять числами TPI | Live AC commands |
| Сезон и heat permission | Существующие HA правила, не автоматический override | Heat enable |
| Одновременные Manual heat+AC | Проверить возможный режим AC/конфликт; предложить явный interlock и согласовать поведение | Live Manual конфликт |
| Потеря HA/AC/датчика, рестарт coordinator | Действующие защиты + recovery policy; запрещён replay старой команды панелью | Приёмка |
| Возврат Auto и отмена Manual | Определить восстановление профиля/уставки без неожиданного включения | Переключение режимов |

Manual switches изменяют виртуальные комнатные requests, не прямой
PWM/реле в обход защиты. Heat ON должен использовать существующий безопасный
room endpoint **из HA coordinator**; AC ON — проверенный режим/уставку внутри HA,
а не случайное последнее состояние.
OFF отключает соответствующую ветвь через её штатный контракт. Два controls
не означают автоматического разрешения конфликтного одновременного нагрева/охлаждения.
До определения interlock показать причину блокировки конфликтного включения,
не выключать другое оборудование скрытой побочной командой.

Смена Auto/Manual подтверждается HA coordinator state. Контролы других комнат,
глобальный источник и исходники TPI не меняются. Перед rollout сравнить их
конфигурацию/профили до и после; пассивно наблюдать, не переключать ради проверки.

### 7.3. Turbo UI

Состояния local `idle/running/finished/stopped`, `duration`, `end_monotonic`.
Продолжительность — параметр UI; окончательное значение/presets отдельно выбрать,
для mock допустима помеченная тестовая длительность. Start запускает отсчёт,
Stop немедленно обнуляет local active state; expiry только завершает UI.
Переходы по страницам не сбрасывают таймер; повтор Start во время running не
создаёт второй таймер. После перезапуска панели — idle (без обещания persistence),
поскольку это демонстрация. На Climate во время turbo остаются реальные HVAC states.
Отдельный тест проверяет **ноль** HA actions от Start/Stop/expiry/navigation/restart.

## 8. Прогноз HA

Источник закреплён владельцем: `weather.yandex_pogoda` — основной,
`weather.home_assistant_gismeteo` — резервный после registry сверки.
Yandex device `5b21c4c47159648ae445a0e92747c8a2`, config entry
`01M2KHM4952FE1PDN3V434GBM0`; Gismeteo device
`fd37f251caf49fbb50dba19adaceb05c`. Met не выбирается автоматически вместо них.
Ссылки владельца: [Яндекс устройство](http://ha.local/config/devices/device/5b21c4c47159648ae445a0e92747c8a2),
[интеграция](http://ha.local/config/integrations/integration/yandex_pogoda#config_entry=01M2KHM4952FE1PDN3V434GBM0),
[Gismeteo устройство](http://ha.local/config/devices/device/fd37f251caf49fbb50dba19adaceb05c).

Fallback выполняется в HA read model по отдельной валидности current/forecast:
при unavailable/ошибке/просроченном primary использовать валидный backup.
Если current и forecast пришли от разных providers, показать источник отдельно
у каждого блока, не склеивать min/max разных providers в один день. Если оба
невалидны — unavailable. Последний успешный Yandex не маркировать свежим во время
fallback. Возвращаться на Yandex после валидного обновления с более новым временем;
не переключать source при каждом repaint. TTL/cache/backoff окончательно задать
по реальной частоте данных обоих providers, не по частоте UI секундомера.

Проверить фактический weather provider и доступный daily forecast. Если forecast
не доступен как subscribed attribute, подготовить HA bridge, который штатно
получает daily forecast и публикует компактные typed поля для панели: timestamp,
local date, condition, temp low/high, precipitation и единицы только при наличии.
Панель не получает новый API key, не обращается к отдельному погодному провайдеру.

Для подтверждённого Yandex источника сначала использовать существующие HA
`forecast_twice_daily`/`forecast_hourly`, не требовать нового внешнего источника.
На 02.11.2026 есть night00:00/day12:00 записи; учитывать `is_daytime`,
`native_temperature`/`native_templow` и timezone. Не называть одну дневную запись
суточными min/max: либо показать отдельно «завтра день/ночь», либо документированно
агрегировать полный доступный набор. Native units нормализовать на HA стороне;
минимум завтра достижим, горизонт 3–5 дней ещё подлежит проверке.

Нормализовать даты по Europe/Moscow, выбирать **завтра**, а не просто второй
элемент массива: провайдер может начинать со следующего дня. Обновление в HA
ограничить cadence провайдера; page show не инициирует запрос. Хранить last success,
last attempt и validity отдельно, чтобы failed refresh не превращал старый forecast
в свежий. TTL/частоту задать после проверки provider, записать в contract.

Ограничить payload 5 daily records; не тащить весь JSON в каждый label. Проверить
единицы ветра/температуры, null/NaN, отсутствие low/high, частичный горизонт,
смену даты, истёкший прогноз и HA outage. Критерий завершения функции — доказанный
прогноз минимум на завтра. Честный placeholder необходим, но сам по себе этот
критерий не закрывает; отсутствие источника фиксируется как блокер live weather.

## 9. Ванная: два надёжных бытовых таймера

Для каждого канала HA хранит persistent absolute deadline, признак активного
заказа, состояние фактического выключателя и состояние подтверждения команды.
Можно использовать existing restored timer helper, но один `timer.finished`
недостаточен для случая, когда срок истёк при остановленном HA: нужна reconciliation.
Deadline/intent принадлежат HA, не ESPHome и не LVGL page.

1. **+1ч:** сериализовать обработку отдельно по каналу. Прочитать актуальный
   deadline; `new_end = max(now, active_deadline) + 3600 s`. Сохранить желание/срок,
   запросить ON штатным endpoint и ждать подтверждённый actuator state.
   Новый deadline может быть принят раньше ON; UI разделяет «таймер задан» и
   «прибор включён». Ошибка ON не скрывается работающим countdown.
2. **Повтор +1ч:** каждое зарегистрированное отдельное касание получает уникальный
   ID `{panel_id, boot_nonce, sequence}` и учитывается, даже пока предыдущий increment
   или ON pending. Generic guard запрета повторного toggle здесь не применяется.
   HA сериализует изменение deadline и дедуплицирует один и тот же event ID;
   три разных события до первого ответа должны дать +3ч. Не применять replay
   после reconnect автоматически. Состояние события unknown после обрыва сверять
   с HA журналом/revision, не создавать новый ID для слепого retry. Два устройства
   обновляют срок через один HA script, не read/modify/write панели. Параллельные
   каналы независимы. Срок хранения/границу dedup ledger явно задать и испытать;
   без persistent dedup не обещать exactly-once через HA restart.
3. **STOP:** идемпотентно отменить свой active intent/deadline и запросить OFF.
   Pending ранее принятого +1ч не должен отменить Stop позже: HA проверяет revision
   заказа; не оставлять очередь старых ON после нового Stop. STOP доступен во время
   обычного pending, если связь позволяет; offline честно показать, что запрос не отправлен.
4. **Expiry:** HA сам запрашивает OFF. Countdown=0 не равно confirmed OFF.
   Если исполнитель unavailable, сохранять desired OFF и ошибку, ограниченно
   повторять через HA reconcile при восстановлении. Не отмечать выключение успешным.
5. **Boot панели:** получить deadline/active/actuator state из HA; ничего не включать.
   При невалидных часах показать «Синхронизация», не выдумывать остаток.
6. **Boot/reload HA:** reconcile persistent deadline и факт нагрузки. Истёкший
   deadline → OFF; будущий deadline → восстановить контроль expiry. Автоматическое
   повторное ON после reboot/внешнего OFF отдельно определить по существующей
   автоматике; безопасный план по умолчанию не включает нагрузку повторно молча.
7. **Внешний OFF:** отменить активный заказ либо показать override согласно
   согласованному контракту, не бороться циклом ON с человеком/защитой.
   Внешний ON без таймера отображать как «Включён без таймера», не придумывать deadline.

Длительность/максимальный накопленный срок/допустимость включения без датчика/
температурные защиты проверить по реальным приборам; никакого искусственного
лимита в UI без документирования. Разрывы между записью deadline и action,
гонки Stop/expiry/+1ч и перезапуск HA испытываются на helpers до настоящих приборов.
При полном отказе HA выключение точно в срок не гарантируется, если нет независимой
защиты исполнителя. Наличие такого fallback проверяется; его отсутствие не скрывать.

## 10. Последовательность маленьких изменений и gates

| Этап | Конкретная работа | Проверка/доказательство завершения | Зависимость |
|---|---|---|---|
| P0: план/инвентаризация | Этот guide, slot evidence, список пробелов; без mutations HA | Решения отражены, неизвестное отделено; текущее состояние не выдано за live без чтения | Выполняется сейчас |
| P1: baseline | Сопоставить Windows/HA source, сохранить dirty/untracked tree, приватно secrets/BIN; capture RH01/living/bedroom текущего source | Manifest revision/hash, 2 RH01 и 3 каждого room legacy PNG, известная панель | Разрешённый старт реализации |
| P2: extraction | Resources → runtime/layout → legacy facade, отдельно шаг за шагом | Config и native всех 3 entry, идентичные legacy PNG при тех же fixtures | P1 |
| P3: UI/mock | Все 5 страниц, navigation/intents, renderer, turbo demo, fixture weather/Auto/Manual; новые captures | Mock transition tests, все состояния PNG, zero HA transport в preview | P2 |
| P4: HA read-only | Living inputs, confirmed light/HVAC, weather forecast bridge candidate при нужде | Единицы/freshness/absence; внешний HA state отображается без обратных commands | Verified inventory; HA additions отдельно review |
| P5: свет | Реальный ручной endpoint, action permission только выбранной панели, pending/timeout | Один tap→один request+немедленный route; автоматика учитывается, HA feedback доказан | P3/P4, разрешённые живые проверки |
| P6: климат | Coordinator contract, helper simulation, ограниченный living package, Auto/Manual | Deadband/interlock/min cycles определены; protection/other rooms invariants соблюдены | AC/heat inventory и согласованные недостающие параметры |
| P7: living acceptance | Полная сборка, отдельная установка, device протокол | Validate/native/BIN текущего source, touch/HA/reconnect/память; фактические evidence | P5/P6/forecast; выбранная панель и разрешение установки |
| P8: bathroom | Profile/home, два HA timer controllers, mock и helpers, затем один device | Два независимых +1ч/Stop/expiry/restart; реальная температура пола/воздуха | Living принят; bath contracts/нагрузки подтверждены |
| P9: rollout | Другие room profiles и прихожая по применимости | Отдельная config/native/BIN/device приёмка каждого изменённого профиля | Не автоматическая часть разрешённой OTA |

P4 read-only и проектирование coordinator можно вести параллельно P2/P3, но
активация live commands зависит от готовности контрактов. Прогноз обязателен до
закрытия P7. Выбранный Comfortaa переносить отдельным шагом после extraction,
выполнить native visual review и обновить functional baseline, не списывать
расхождения на HA работу.
За один шаг менять один слой; после успешных проверок не повторять полный набор
без новых изменений/ошибок. Не устанавливать ESP32 SDK/SDL/noVNC на Windows.

## 11. Распределение работ между агентами

В планировании запущены три **gpt-6.1-sol** субагента:

| Направление | Область владения | Выход |
|---|---|---|
| HA inventory | Read-only HA/infra/climate; один новый inventory report | Сущности/capabilities/автоматика/evidence, неизвестное |
| UI architecture | Read-only source/IDs/merge/adapter design | Рекомендации по tree/contracts и опасным событиям |
| Validation | Read-only runbook/tests/Workshop API | Проверки/gates/rollback и пределы доказательств |
| Ведущий агент | Только новый guide и последующее согласованное связывание документов | Сводный план, устранение противоречий |

При реализации передавать изолированные задачи с owned files, входным контрактом,
критерием готовности и запретами. UI agent владеет pages/resources; state agent —
reducer/mock/tests; HA agent — candidates/bindings; интегратор — composition/events/
manifest и review. Общие файлы одновременно не редактировать. HA mutations и
задания Workshop сериализуются одним ответственным агентом. Субагентам не даётся
самостоятельное право включать нагрузки или менять thermostat firmware.

## 12. Проверки и критерии приёмки

### 12.1. Проверки без реальных нагрузок

| ID | Сценарий | Ожидаемое доказательство |
|---|---|---|
| UI-01 | Legacy extraction | RH01/living/bedroom старые fixtures, PNG совпадают; IDs уникальны |
| NAV-01 | Все routes, Home/Back, System из вторичной, повтор/переполнение | Предсказуемая bounded history, ни одного HA action |
| CMD-01 | Tap лампы, быстрый второй tap, page-load, render, hold | Один запрос на принятое касание; route немедленно; 0 побочных запросов |
| CMD-02 | Offline/unknown/pending/timeout/late feedback/reconnect | Навигация доступна; нет queue/replay; confirmed value не выдуман |
| CMD-03 | Внешний state/brightness/setpoint update | UI меняется без обратной service call; release slider отправляет один intent |
| DATA-01 | Missing/unavailable/stale/NaN/крайние значения | Различимые состояния, единицы/округление, нет 0 вместо missing |
| HVAC-01 | Auto deadband boundaries/heat↔cool/min cycles | Coordinator не включает противостоящие ветви и соблюдает подтверждённые пределы |
| HVAC-02 | Manual switches/OFF/сезон/protection/stale sensor | Нет bypass; mode/actual separate; другой room/global source не меняются |
| ROOM-01 | Неверная area/binding, две панели разных комнат | Commands ограничены своей room allowlist, общего area-wide toggle нет |
| HVAC-03 | Панель offline/reboot, изменение helper из HA dashboard | Coordinator работает независимо; 0 прямых HVAC writes/default resets панели |
| TURBO-01 | Start/Stop/expiry/navigation/reboot | Countdown верен; **0 HVAC/HA actions** во всех случаях |
| WX-01 | 1/3/5 дней, нет today, null low, смена даты, refresh fail | Завтра найден по дате, stale видим, нет fictional forecast |
| BATH-01 | +1ч/+1ч, два канала; три события до ACK с двух панелей; duplicate ID | +3ч для трёх уникальных событий, duplicate не добавляет час, второй канал не меняется |
| BATH-02 | Stop во время ON pending/expiry/+1ч гонка, late ON ACK | Последний Stop не отменён старой очередью, OFF подтверждается отдельно, late ACK не возрождает deadline |
| BATH-03 | Navigation/reboot панели/HA down через deadline | HA владеет сроком; boot reconcile; countdown 0 не выдаётся за OFF |
| VIS-01 | Все страницы/состояния, крайние строки и выбранный шрифт | Нет clipping, Cyrillic glyphs есть, home geometry сохранена |

Mock timestamps и trace command counts фиксировать в результатах. Native PNG
доказывает отрисовку, но не физический touch. Не считать Python mock worker тест
компиляцией прошивки. Для reducers использовать реальный production код или
проверять его через host harness, а не тестировать вторую реализацию алгоритма.

### 12.2. Существующие операции проверки

Из корня FormaPanel, в подготовленной среде Python:

```sh
python tools/validate.py
python -m unittest discover -s tests -v
git diff --check
```

Это static/asset/unit проверки. Новые C++ tests запускать через доступный host
toolchain HA/CI; не устанавливать тяжёлые SDK локально. Если появились новые
resources, включить их в manifest/проверки и воспроизводимый render workflow.
В текущем дереве 11 tests: 3 asset pipeline, 4 RH01, 4 Workshop; проверок новых
bindings/navigation/HVAC runtime ещё нет. Они создаются в P3–P6, не объявляются
прошедшими по существующему зелёному CI.

В HA Workshop выбрать **living**, последовательно:

1. **Проверить** — `esphome config`, PASS по firmware entry.
2. **Обновить предпросмотр** — native config + compile + запуск LVGL + все PNG.
   У каждого нового scenario свой snapshot filename; сохранить completion marker
   `RH01_NATIVE_PREVIEW_COMPLETE`. Ожидать LVGL flush перед snapshot.
3. **Собрать прошивку** — config + compile аппаратного entry. Сохранить приватно
   factory/OTA, SHA-256, размер, job ID, profile, source fingerprint/revision.

Существующий API через HA Ingress: `POST api/jobs` с
`{"kind":"validate","profile":"living"}`; затем `preview` и `firmware`,
опрос `GET api/state?profile=living`. Не сохранять временный Ingress URL.
Worker применяет стабильный `/data/configs/<kind>-living.yaml` wrapper, не
собирать package profile как самостоятельный entry. Downloads:
`files/<job-id>/firmware.factory.bin` и `files/<job-id>/firmware.ota.bin`.

**Дополнительный gate поверх текущего server.py:** native success сейчас требует
лишь ≥2 BMP, а firmware success — хотя бы один найденный BIN. Для приёмки явно
проверять **весь expected capture manifest** и **оба factory/OTA BIN** с хешами.
Минимальный новый manifest: home-on/off/unknown; lighting-confirmed/pending/error/
unavailable; climate-auto/manual/blocked/pending; turbo-idle/running/stopped/expired;
weather-current-forecast/tomorrow/partial/unavailable/fallback; system-connected/
offline; bathroom-two-active/one-stopped/expired-off-pending/unavailable/recovered.
Сценарии добавляются по этапам; каждый filename уникален, отсутствующий кадр
проваливает gate даже при зелёном статусе worker.

Source paths: `targets/living.yaml`, `previews/living.yaml`; в Workshop manifest
пути начинаются с `firmware/esphome/`. Аналогично bathroom после добавления.
Legacy rh01/bedroom повторно проверять при изменении shared resources/layout.
Один job одновременно; HTTP 409 означает занятость, не повод обходить очередь.
Прежний успешный BIN/PNG после нового failed job не является новым результатом.
Stale preview не принимается. Workshop не выполняет OTA.

### 12.3. Живая HA и аппаратная приёмка

До установки подтвердить физическую living панель, device identity/API entry,
точный текущий BIN/source и возможность восстановления. Не считать имя профиля
доказательством физической комнаты. Получить разрешение на установку именно этой
панели и обозначенные тесты нагрузок; не повторять уже полученное разрешение.

Порядок: input-only → один световой round-trip → внешний state из HA →
разрешённые HVAC intents → отказ/восстановление связи только выбранной панели.
Не отключать весь HA или климат квартиры ради reconnect теста; destructive/outage
опыты сначала в mocks/helpers, реальный способ отказа отдельно согласовать.
Отмечать времена request/feedback, источник и expected predicate, число commands.
Сравнить before/after living и остальных комнатных профилей/глобального источника;
изменения измерений при обычной работе не считать непрошенным изменением настройки.

На устройстве проверить touch hit areas/короткое касание/удержание, быстрые повторы,
Home/Back, slider release, кириллицу, яркость, wake/start, смену состояния из HA,
потерю датчика/HA, reconnect без replay, поведение pending и turbo. Снять heap/PSRAM,
reset reason и наблюдение за утечкой при циклической навигации. Интервал и
критерии стабильности записать до испытания; численных FPS/памяти заранее не обещать.
Плановый первый soak — 2 часа навигации/обычных обновлений и наблюдение в течение
суток; это цель будущей проверки, не уже полученное доказательство надёжности.

Для ванной expiry проверять ускоренными helper fixtures, затем согласованным
реальным циклом. Реальный HA restart не требуется для разработки: восстановление
отдельно моделировать; эксплуатационный reboot только с разрешением по правилам.

## 13. Сохранение, откат и критерии остановки

Перед изменением существующего source сохранить датированную копию каждого
затрагиваемого файла и manifest хешей; сохранить untracked файлы, не только diff.
Secrets и BIN — отдельно приватно, без ссылок на публичный upload. Source backup
не должен попадать в compilation includes. Не использовать `git reset --hard`,
clean, overlay чужого checkout или массовую синхронизацию поверх dirty tree.

| Сбой | Действие восстановления | Проверка |
|---|---|---|
| UI regression | Восстановить только owned изменённые файлы из датированного backup, сохранив более новые чужие правки | Config/native baseline, diff |
| Failed job | Сохранить log/job metadata, исправить первую причину, повторить нужную операцию | Новый success/current artifact; cache целиком не удалять |
| HA package regression | По подготовленному rollback отключить только новый package/automation и восстановить его previous config | HA validation, scoped reload если поддерживается, read-only состояния |
| Pending/relay mismatch | Прекратить новые команды; сверить HA и executor, использовать штатное управление владельца | Confirmed state, отсутствие повторной очереди |
| Firmware regression | После согласованной процедуры вернуть сохранённый BIN именно этой панели | Boot/API/touch/версия; не OTA всех панелей |
| Unexpected cross-room/global change | Остановить live этап, сохранить безопасный trace, восстановить только доказанно изменённую настройку по rollback | Не повторять команду до устранения причины |

Перед HA rollback учесть активные towel deadlines: удаление новой automation
не должно оставить включённые приборы без владельца выключения. Сначала передать
контроль существующему механизму либо согласованно завершить активные заказы с
подтверждённым OFF. Нельзя считать rollback только возвратом YAML.

Не продолжать live этап при неизвестном entity/несовпадении device identity,
невалидной температуре, неопределённой автоматике света, отсутствии понятного
OFF/recovery или неожиданном изменении чужой комнаты. Это не блокирует независимую
mock/visual работу. Не чинить сеть/HA Core/инфраструктуру в рамках UI задачи молча.

## 14. Как фиксировать результат

Для каждого этапа: дата MSK, профиль/панель, source revision + dirty manifest,
изменённые файлы, backup/rollback, команды/настройки без secrets, test IDs и
PASS/FAIL/NOT RUN, Workshop job/fingerprint/hash, PNG/фото/обезличенный trace,
известные пробелы. Плановые чекбоксы не отмечать по факту написания документа.

Living завершён только когда есть реальные inputs, прогноз минимум завтра,
согласованный свет с подтверждением, реализованный HA Auto/Manual, честная
turbo-заглушка, все navigation states и отдельная device приёмка. Ванная остаётся
обязательным следующим результатом, а не скрытым необязательным backlog.

Текущее выполнение этого документа: составление инструкции и read-only исследование.
Новые UI packages, HA coordinator/forecast/towel packages, сборки и установки
**ещё не выполнены**. Фактические findings и дальнейшие blockers отражаются в
отчёте инвентаризации и последующих validation reports.

### 14.1. Результат текущего подготовительного этапа

Созданы guide и inventory, исходный план связан с ними и дополнен последними
решениями virtual HVAC/room context/Yandex→Gismeteo. Архитектура и gates проверены
тремя субагентами; замечания про duplicate events, Stop при pending, полноту
captures и обоих BIN включены. Live GET/registry evidence подтверждает входные
данные и прогноз завтра; бытовые actions/HA writes/сборки/OTA не выполнялись.

Backup исходного плана и раннего guide перед связыванием:
`Home/local/backups/formapanel-ui-plan-20261101-111600/`; inventory agent сохранил
свои датированные private backups. Откат документации — точечный возврат этих
файлов после сравнения с более новыми правками, без затрагивания firmware.
Дальнейшая реализация выполняет P1–P8 с перечисленными gates; этот раздел не
отмечает их выполненными.

Проверка подготовленных документов: локальные ссылки существуют, fenced blocks
закрыты, trailing whitespace отсутствует; `git diff --check` без ошибок diff.
Полная firmware/unit проверка не запускалась: изменена только документация,
runtime исходники в этой сессии не изменялись. Последние решения о Comfortaa,
виртуальном HVAC и источниках погоды включены в оба плана.
