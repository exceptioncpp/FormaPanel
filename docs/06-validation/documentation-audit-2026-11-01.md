# Аудит документации FormaPanel — 01.11.2026

Запрос: проверить инфраструктуру разработки, методологию, основу и принципы
компоновки прошивки, сборку; дополнить отсутствующее. Проверялось состояние
текущего проекта и относящейся к нему среды HA, не всех сервисов Home.

## Покрытие после исправления

| Область | Документ и содержание |
|---|---|
| Точка входа | [Начать здесь](../development.md): порядок чтения, первая итерация, факт/план |
| Инфраструктура | [HA Workshop runbook](../../../../docs/infrastructure/ha-formapanel-workshop.md): узел/версии/пути, установка, update/rebuild, cache/env, Git, secrets, backup/recovery |
| Основа и слои | [Архитектура](../04-architecture/architecture.md): ESPHome/LVGL, server/host/device, текущая реализация и целевой HA flow |
| Компоновка исходников | [Source composition](../04-architecture/source-composition.md): дерево и include graph, board/entry/profile/UI/backend, merge/IDs, paths, новые страницы и варианты |
| Методология | [Практический UI workflow](../02-research/effective-ui-development-2026-11.md): прямой YAML, generated fragment, mocks/HA, visual editors, интерактивные кандидаты |
| Сборка | [Build/preview runbook](build-and-preview-runbook.md): checkout, provisioning, manifest, Validate/native/BIN, результаты/логи, recovery, локальные checks и границы CI |
| Доказательства | [Первичная Workshop](ha-workshop-2026-10-31.md), [incremental 0.1.1](ha-workshop-incremental-2026-11-01.md), [план/статус тестов](test-plan.md) |

## Исправленные пробелы и противоречия

- Архитектура больше не называет ESPHome прошивку нереализованной; отдельно
  указаны существующие demo UI/network/diagnostics и будущие бытовые bindings.
- Прежний build proposal с Windows SDK, версией 2026.10.0 и отсутствующими
  `panels/living-rh01.yaml` заменён актуальным процессом HA. Тяжёлые SDK
  на Windows не требуются. Native C-кандидат остаётся отдельным направлением.
- Планы A/B/S0, исследование редакторов и старый JS preview направляют читателя
  к настоящему host/snapshot и не подменяют аппаратную приёмку.
- Описаны отсутствие повторного включения home, ID-контракт info/capture,
  различающиеся asset roots исходного entry и targets/previews, package-local
  secrets. Исправлен комментарий публичного `secrets.yaml.example`.
- Проговорено, что RH-01 host имеет отдельные fixed demo substitutions;
  living/bedroom используют один профиль в device и host.
- Разделены update после version bump и rebuild без изменения version;
  backup worker `/data` не считается backup общего source/working tree/secrets.
- Уточнены stale/старые артефакты после ошибки и необходимость вручную
  включать новые страницы в capture-сценарий.
- Удалены устаревшие утверждения о непроверенных сборках и отсутствии SPI в
  нынешнем S0 template. Roadmap отделяет готовую серверную среду от железа/CI.
- Корневые README и общая документация Home ведут в одну карту разработки.

## Проверка

Сопоставлены реальные YAML, manifest, worker 0.1.1, tests и `verify.yml`.
Read-only HA проверка подтвердила installed/latest Workshop **0.1.1**,
Ingress/sidebar и работающий контейнер. Сервисы/прошивка не перенастраивались.

Проверены относительные Markdown file targets в документах репозитория
и общих точках входа Home; отсутствующих целей нет. Это проверка локальных
ссылок, не доступности всех внешних сайтов. `tools/validate.py` и
`git diff --check` проходят. Исторические отчёты о конкретных сборках сохранены
как датированные результаты, не переписаны в новые доказательства.

Подробные локальные результаты проверки ссылок находятся в игнорируемом
`reports/local/documentation-audit-2026-11-01.json`.
Документы точечно синхронизированы с общим checkout HA с проверкой исходных
hashes; без наложения всего проекта и без записи private credentials.

## Backup и границы

Исходные документы сохранены под `Home/local/backups/`:
`formapanel-doc-audit-20261101-104244` и
`formapanel-runbook-audit-20261101-104206`.
Откат документации — вернуть только затронутые документы из backup либо
осознанного Git revision; настройки приложений и устройство отката не требуют.

SDL/noVNC, Save → auto-build, полный visual round-trip, HA adapters и реальные
device tests описаны как предложения/следующие гейты. Их наличие в документе
не означает внедрение. Firmware CI отсутствует: текущий workflow выполняет
asset generation, static validator и unit tests.
