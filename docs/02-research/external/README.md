# Внешний отчёт, предоставленный пользователем

`deep-research-report-2026-10-31.md` — неизменённая копия файла
`deep-research-report.md`, переданного 31.10.2026. SHA-256 исходника:
`52c2a78223961f2d603aa1b08b865a5ff74deaeeac269738e3c6c5bd1e534199`.

Документ рассматривается как исследовательский материал, не как инструкция
менять установленную инфраструктуру. Его внутренние маркеры `turn…` — ссылки
из другого сеанса, а не доступные доказательства в текущем проекте.

## Что учтено в решении FormaPanel

- Вывод о том, что единого браузерного WYSIWYG для произвольного многофайлового
  ESPHome/LVGL проекта с надёжным round-trip нет, совпадает с нашей проверкой.
  Установленный Designer RC48 не раскрывает `!include`; LVGL-картинки имеют
  ограничения. Структура файлов остаётся под управлением Studio Code Server/Git.
- Разделение общих ресурсов, страниц, bindings и профилей принято. Привязки
  должны ссылаться на стабильные ID, а разные устройства включать общие страницы.
- UI-фрагмент из визуального редактора можно изучать отдельно. Это не означает
  импорт/экспорт всей прошивки и не заменяет прямое редактирование checkout.
- Для текущей задачи native ESP-IDF не требуется: мы уже проверили **настоящий
  LVGL preview из существующего ESPHome YAML** через `host` + `snapshot` на HA.
  Этот путь не отражён в рекомендованном workflow отчёта, но устраняет зависимость
  от отдельного browser renderer и ручного переноса UI между средами.
- SquareLine **1.6.3 от 30.10.2026 с LVGL 9.6** подтверждён официальным changelog.
  Это уточняет прежнее исследование 29.10, где фигурировал 1.6.2. Смена версии
  SquareLine не добавляет экспорт ESPHome YAML, поэтому выбор среды не меняет.
- Фактический baseline FormaPanel — ESPHome **2026.10.1** и LVGL **9.5.0**,
  проверенные в используемой среде. Упоминание новых upstream версий не служит
  основанием обновлять рабочий baseline посреди проверки.

Решение: [ADR-0004](../../04-architecture/adr/0004-browser-workshop.md).
Фактический [native preview](../../06-validation/rh01-native-preview-2026-10-31.md).

## Уточнение 01.11.2026

Отсутствие импорта всего дерева packages в visual editor не препятствует
редактированию одного UI-фрагмента. ESPHome штатно расширяет вложенные
LVGL pages/widgets через `!extend`, поэтому внешний вид и ручные HA bindings
можно хранить отдельно. Важен тест сохранения ID и поддерживаемых свойств.

Найден дополнительный мост
[SquarelineToEsphome](https://github.com/gpambrozio/SquarelineToEsphome):
он читает `.sqproj` и пишет YAML, в том числе в режиме `--monitor`.
Поэтому вывод «SquareLine возможен только после перехода на ESP-IDF» слишком
категоричен: сторонний путь сохранения ESPHome существует. В нашем pinned
стеке он ещё не проверен; полный round-trip и совместимость не подтверждены.
LVGL Pro по-прежнему работает с XML/native C, прямого штатного YAML pipeline
для нашего проекта не установлено.

[LCD Wizard](https://lcdwizard.com/docs/esphome) — ещё один кандидат с ESPHome
экспортом, simulated inputs и HA actions. Его exporter ориентирован на полный
проект; автор прямо отделяет проверку config/generated C++ от испытаний с HA.
В FormaPanel он не внедрялся. Подробный [практический процесс](../effective-ui-development-2026-11.md)
содержит готовые и предложенные варианты отдельно.

Первичные источники:
[ESPHome snapshot](https://esphome.io/components/display/snapshot/),
[ESPHome host](https://esphome.io/components/host/),
[Designer README](https://github.com/koosoli/ESPHomeDesigner),
[ESPBoards export](https://lvgl.espboards.dev/help/guide/add-lvgl-design/),
[SquareLine changelog](https://docs.squareline.io/docs/miscellanos/changelog/).
