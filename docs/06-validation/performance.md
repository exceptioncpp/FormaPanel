# Performance budgets and measurement protocol

**Нет текущих измерений на реальном Guition.** Числа ниже — инженерные ориентиры/формулы, не гарантии.

## Buffer math

RGB565 480²×2 = 460,800 B (450 KiB); 720²×2 = 1,036,800 B (~1,013 KiB). RGB8888/ARGB8888 ×4 = 900 KiB и ~2,025 KiB. Не путать framebuffer с total heap/PSRAM: нужны draw buffers, image cache, Wi-Fi stack, LVGL heap.

## Target monitoring

- Free internal heap, max allocated block, free PSRAM, PSRAM fragmentation.
- Flash occupancy, image assets total size, time to load/switch page.
- Frame time p50/p95/p99, UI touch-to-feedback delay, dropped frames.
- Idle Wi-Fi update activity and draw calls; при отображении неподвижной страницы экран не должен бессмысленно перерисовываться.
- Отдельно замерять «полноэкранная фотография», «градиент + частичное обновление», «анимация», «декодирование изображений», «навигация между 3 страницами».

## Acceptance thresholds

Порог FPS и RAM определить после первого прототипа по real device measurements, не фиксировать недоказанные цифры. Первичный UX-ориентир: отклик на касание воспринимается мгновенным (<150–200 ms как гипотеза для проверки), без видимых зависаний при смене страниц.
