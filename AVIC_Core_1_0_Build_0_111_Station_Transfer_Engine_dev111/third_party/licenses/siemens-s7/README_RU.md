# Siemens S7 — исторический license inventory

Дата пересмотра: 27.11.2026

## Важное изменение политики

Ранее исследованные Python packages (python-snap7, s7commplus) **не являются выбранными runtime-зависимостями AVIC**. Их license files и notices оставлены в репозитории как исторический материал аудита; они не разрешают добавлять Python S7 engine в продукт.

S7NetPlus (.NET) также не является выбранным движком.

## Исторически проверенные материалы

- python-snap7 — MIT; upstream: https://github.com/gijzelaerr/python-snap7
- s7commplus — package MIT; upstream: https://github.com/gijzelaerr/s7commplus
- S7CommPlusDriver zlib preset dictionaries — отдельный LGPL-3.0-or-later notice.
- HarpoS7 V1 SessionKey helper — отдельный MIT notice.
- S7.Net Plus — MIT; .NET implementation, не соответствует C-only runtime policy.

## Кандидаты C

- Snap7: https://github.com/davenardella/snap7 — C++ core/toolchain, LGPL-3.0 licensing materials. Требует точного file-level audit; не маркировать pure C.
- libnodave: https://github.com/netdata-be/libnodave — C, LGPL-2.0-or-later library sources; upstream beta warning, historical compatibility and safety review required. GPL tools must be excluded or separately inventoried.

## Правило поставки

До выбора конкретного C engine:
- S7 optional dependencies отсутствуют в pyproject;
- никакой Python/Rust S7 fallback не запускается;
- S7 остаётся PLANNED;
- все сохранённые license texts считаются архивными аудит-материалами, а не разрешением на включение соответствующего runtime.

Для любого будущего релиза требуется закрепить upstream commit, выполнить file-level license scan, SBOM, dependency audit и проверить способ динамической/статической линковки. Этот документ не является юридическим заключением.
