"""Curated original isometric 3D HVAC/ITP SVG library for AVIC Graphics Workbench.

SVG artwork is original AVIC vector illustration inspired by common HVAC/BMS
orthographic graphics conventions. It does not bundle or reproduce proprietary
Niagara/third-party symbol files. Existing symbol IDs remain stable.
"""
from __future__ import annotations
from pathlib import Path

SVG_DIR = Path(__file__).resolve().parents[1] / "ui" / "static" / "svg-library"

# Stable IDs are persisted in GraphicElement.symbol_key. Existing IDs are preserved.
SVG_SYMBOLS: dict[str, dict[str, str]] = {
    'fan': {'name': 'Вентилятор осевой канальный', 'category': 'Вентиляция', 'description': 'Осевой канальный вентилятор с мотором и ротором', 'tags': 'вентилятор осевой канальный fan motor rotor', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'air_handling_unit': {'name': 'Приточная установка ПВУ в разрезе', 'category': 'Вентиляция', 'description': 'Изометрический разрез ПВУ: фильтр, теплообменная секция и вентилятор', 'tags': 'пву ahu приточная установка секция вентиляция разрез', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'filter': {'name': 'Фильтр кассетный', 'category': 'Фильтрация', 'description': 'Кассетный фильтр в корпусной секции воздуховода', 'tags': 'фильтр кассетный карманный очистка воздуха', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'heating_coil': {'name': 'Калорифер водяной', 'category': 'Теплообменные секции', 'description': 'Секция нагрева с красным контуром подачи теплоносителя', 'tags': 'нагреватель калорифер тепло горячая вода красный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'cooling_coil': {'name': 'Охладитель водяной', 'category': 'Теплообменные секции', 'description': 'Секция охлаждения с синим контуром холодоносителя', 'tags': 'охладитель испаритель холодная вода синий', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'heat_recovery': {'name': 'Роторный рекуператор', 'category': 'Теплообменные секции', 'description': 'Роторный теплоутилизатор в корпусе воздуховода', 'tags': 'рекуператор роторный теплоутилизация', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pump': {'name': 'Насос консольный с электродвигателем', 'category': 'ИТП · насосы', 'description': 'Центробежный насос с электродвигателем и фланцами', 'tags': 'насос насосный агрегат pump', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pump_vertical': {'name': 'Насос вертикальный многоступенчатый', 'category': 'ИТП · насосы', 'description': 'Вертикальный многоступенчатый насос', 'tags': 'насос вертикальный многоступенчатый', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pump_inline': {'name': 'Насос линейный inline', 'category': 'ИТП · насосы', 'description': 'Линейный насос в разрыв трубопровода', 'tags': 'насос линейный inline циркуляционный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'valve': {'name': 'Клапан двухходовой', 'category': 'ИТП · арматура', 'description': 'Двухходовой клапан в изометрической трубной обвязке', 'tags': 'клапан двухходовой запорная арматура', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'control_valve': {'name': 'Клапан регулирующий с приводом', 'category': 'ИТП · арматура', 'description': 'Регулирующий клапан с электроприводом', 'tags': 'клапан регулирующий привод двухходовой', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'three_way_valve': {'name': 'Клапан трёхходовой', 'category': 'ИТП · арматура', 'description': 'Смесительный трёхходовой клапан', 'tags': 'клапан трехходовой смешение', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'damper': {'name': 'Заслонка воздушная регулирующая', 'category': 'Воздушные заслонки', 'description': 'Одна поворотная лопатка в прямоугольном воздуховоде, электропривод', 'tags': 'заслонка воздушная регулирующая actuator damper', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'sensor': {'name': 'Датчик расхода канальный', 'category': 'КИП · датчики', 'description': 'Канальный датчик с погружным элементом', 'tags': 'датчик расхода воздух', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'temperature_sensor': {'name': 'Датчик температуры', 'category': 'КИП · датчики', 'description': 'Гильза и головка датчика температуры', 'tags': 'датчик температура термодатчик', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pressure_sensor': {'name': 'Датчик давления', 'category': 'КИП · датчики', 'description': 'Импульсная трубка и датчик давления', 'tags': 'датчик давления pressure', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'flow_sensor': {'name': 'Расходомер', 'category': 'КИП · датчики', 'description': 'Врезной датчик расхода на трубопроводе', 'tags': 'расходомер расход flow meter', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'thermometer': {'name': 'Термометр технический', 'category': 'КИП · приборы', 'description': 'Термометрический прибор на патрубке', 'tags': 'термометр температура', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pressure_gauge': {'name': 'Манометр технический', 'category': 'КИП · приборы', 'description': 'Стрелочный манометр на отводе', 'tags': 'манометр давление gauge', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'heat_exchanger': {'name': 'Пластинчатый теплообменник', 'category': 'ИТП · теплообменники', 'description': 'Разборный пластинчатый теплообменник с красным и синим контурами', 'tags': 'итп теплообменник пластинчатый горячая холодная вода', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'boiler': {'name': 'Котёл водогрейный', 'category': 'ИТП · источники тепла', 'description': 'Напольный водогрейный котёл', 'tags': 'котел водогрейный boiler', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'chiller': {'name': 'Чиллер воздушного охлаждения', 'category': 'Холодоснабжение', 'description': 'Чиллер с вентиляторами конденсатора', 'tags': 'чиллер холодильная машина охлаждение', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'tank': {'name': 'Бак расширительный мембранный', 'category': 'ИТП · ёмкости', 'description': 'Вертикальный мембранный расширительный бак', 'tags': 'бак расширительный мембранный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'compressor': {'name': 'Компрессор холодильный', 'category': 'Холодоснабжение', 'description': 'Компрессорный агрегат', 'tags': 'компрессор refrigeration', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pipe': {'name': 'Труба прямая изометрическая', 'category': 'Трубопроводы', 'description': 'Изометрический участок трубопровода с фланцевыми концами', 'tags': 'труба трубопровод прямая изометрия', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pipe_elbow': {'name': 'Отвод трубопровода 90°', 'category': 'Трубопроводы', 'description': 'Изометрический отвод с плавным радиусом', 'tags': 'труба отвод колено elbow', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pipe_tee': {'name': 'Тройник трубопровода', 'category': 'Трубопроводы', 'description': 'Изометрический трубный тройник', 'tags': 'тройник трубопровод tee', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct': {'name': 'Воздуховод прямоугольный', 'category': 'Воздуховоды и секции', 'description': 'Прямой участок оцинкованного прямоугольного воздуховода', 'tags': 'воздуховод прямоугольный duct прямой', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct_elbow': {'name': 'Отвод воздуховода 90°', 'category': 'Воздуховоды и секции', 'description': 'Прямоугольный изометрический отвод с большим радиусом', 'tags': 'воздуховод отвод колено 90', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct_transition': {'name': 'Переход воздуховода', 'category': 'Воздуховоды и секции', 'description': 'Переход с большого сечения на малое', 'tags': 'воздуховод переход редукция', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct_tee': {'name': 'Тройник воздуховода', 'category': 'Воздуховоды и секции', 'description': 'Тройниковое ответвление прямоугольного воздуховода', 'tags': 'воздуховод тройник ответвление', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct_cross': {'name': 'Крестовина воздуховода', 'category': 'Воздуховоды и секции', 'description': 'Крестовое соединение воздуховодных трасс', 'tags': 'воздуховод крестовина разветвление', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'duct_round': {'name': 'Воздуховод круглый', 'category': 'Воздуховоды и секции', 'description': 'Круглый металлический воздуховод', 'tags': 'воздуховод круглый оцинкованный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'damper_parallel': {'name': 'Заслонка параллельные лопатки', 'category': 'Воздушные заслонки', 'description': 'Многолопаточная заслонка с параллельным поворотом', 'tags': 'заслонка многолопаточная параллельная', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'damper_opposed': {'name': 'Заслонка встречные лопатки', 'category': 'Воздушные заслонки', 'description': 'Многолопаточная заслонка с встречным поворотом', 'tags': 'заслонка встречные лопатки opposed', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fire_damper': {'name': 'Клапан противопожарный', 'category': 'Воздушные заслонки', 'description': 'Противопожарная заслонка с огнестойкой рамой и приводом', 'tags': 'клапан противопожарный огнезадерживающий', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'smoke_damper': {'name': 'Клапан дымоудаления', 'category': 'Воздушные заслонки', 'description': 'Дымовой клапан с приводом и усиленной рамой', 'tags': 'клапан дымовой дымоудаление', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fan_centrifugal': {'name': 'Вентилятор радиальный улиточный', 'category': 'Вентиляторы', 'description': 'Центробежный вентилятор с рабочим колесом в улитке', 'tags': 'вентилятор радиальный центробежный улитка', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fan_belt_drive': {'name': 'Вентилятор ременной привод', 'category': 'Вентиляторы', 'description': 'Вентилятор с отдельным электродвигателем и ременной передачей', 'tags': 'вентилятор ременной привод двигатель', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fan_plug': {'name': 'Вентилятор plug fan', 'category': 'Вентиляторы', 'description': 'Свободно вращающееся рабочее колесо с прямым приводом', 'tags': 'вентилятор plug fan свободное колесо', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fan_roof': {'name': 'Вентилятор крышный', 'category': 'Вентиляторы', 'description': 'Крышный вытяжной вентилятор с защитным колпаком', 'tags': 'вентилятор крышный вытяжной', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'fan_twin': {'name': 'Вентиляторная секция сдвоенная', 'category': 'Вентиляторы', 'description': 'Два осевых вентилятора в единой секции', 'tags': 'вентилятор сдвоенный двойной', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'filter_bag': {'name': 'Фильтр карманный', 'category': 'Фильтрация', 'description': 'Карманный фильтр с отдельными фильтрующими пакетами', 'tags': 'фильтр карманный bag filter', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'silencer': {'name': 'Шумоглушитель канальный', 'category': 'Фильтрация и обработка', 'description': 'Канальный пластинчатый шумоглушитель', 'tags': 'шумоглушитель вентиляция акустика', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'humidifier': {'name': 'Увлажнитель канальный', 'category': 'Фильтрация и обработка', 'description': 'Канальный секционный увлажнитель с форсунками', 'tags': 'увлажнитель форсунки паровой', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'shell_tube_exchanger': {'name': 'Кожухотрубный теплообменник', 'category': 'ИТП · теплообменники', 'description': 'Горизонтальный кожухотрубный теплообменник', 'tags': 'теплообменник кожухотрубный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pump_group_dual': {'name': 'Насосная группа сдвоенная', 'category': 'ИТП · насосные группы', 'description': 'Два насоса на общей раме с коллекторами', 'tags': 'насосная группа два насоса итп', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'pump_group_triple': {'name': 'Насосная группа тройная', 'category': 'ИТП · насосные группы', 'description': 'Три насоса на общей раме с коллекторами', 'tags': 'насосная группа три насоса итп', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'strainer': {'name': 'Фильтр сетчатый Y', 'category': 'ИТП · арматура', 'description': 'Y-образный сетчатый фильтр трубопровода', 'tags': 'фильтр сетчатый грязевик итп', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'butterfly_valve': {'name': 'Затвор дисковый поворотный', 'category': 'ИТП · арматура', 'description': 'Дисковый затвор с приводом', 'tags': 'затвор дисковый бабочка butterfly', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'balance_valve': {'name': 'Клапан балансировочный', 'category': 'ИТП · арматура', 'description': 'Балансировочный клапан с измерительными штуцерами', 'tags': 'клапан балансировочный', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'air_separator': {'name': 'Сепаратор воздуха', 'category': 'ИТП · ёмкости', 'description': 'Вертикальный сепаратор воздуха с воздухоотводчиком', 'tags': 'сепаратор воздуха итп', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'heat_meter': {'name': 'Теплосчётчик', 'category': 'ИТП · приборы', 'description': 'Вычислитель с парой датчиков температуры и расходомером', 'tags': 'теплосчетчик узел учета тепла', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'itp_heating_substation': {'name': 'ИТП отопление', 'category': 'ИТП · узлы в сборе', 'description': 'Изометрическая компоновка отопительного теплового пункта: теплообменник, насосы, коллекторы и КИП', 'tags': 'итп отопление тепловой пункт узел в сборе', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'itp_dhw_substation': {'name': 'ИТП ГВС', 'category': 'ИТП · узлы в сборе', 'description': 'Изометрическая компоновка узла ГВС с двумя теплообменными пакетами и насосами', 'tags': 'итп гвс горячее водоснабжение теплообменник', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'cooling_tower': {'name': 'Градирня вентиляторная', 'category': 'Холодоснабжение', 'description': 'Вентиляторная градирня с оросителем', 'tags': 'градирня охлаждение вентилятор', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'expansion_vessel': {'name': 'Гидроаккумулятор', 'category': 'ИТП · ёмкости', 'description': 'Мембранный гидроаккумулятор для гидравлического контура', 'tags': 'гидроаккумулятор бак', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'mixing_unit': {'name': 'Смесительный насосный узел', 'category': 'ИТП · узлы в сборе', 'description': 'Смесительный узел с подачей и обраткой и насосной группой', 'tags': 'смесительный узел насос итп', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
    'differential_pressure_controller': {'name': 'Регулятор перепада давления', 'category': 'ИТП · арматура', 'description': 'Автоматический регулятор перепада давления на подающем трубопроводе', 'tags': 'регулятор перепада давления клапан', 'visual_style': 'isometric-3d', 'view': 'orthographic-isometric'},
}


# Modular cutaway air-handling-unit sections. All seven modules share a common
# cabinet envelope, front cutaway, viewBox, and mating flange coordinates.
SVG_SYMBOLS.update({
    "ahu_section_outdoor_damper": {
        "name": "ПВУ · Секция заслонки наружного воздуха",
        "category": "ПВУ · модульные секции",
        "description": "Модуль корпуса ПВУ с многолопаточной заслонкой наружного воздуха и электроприводом; положение лопаток анимируется от BOOL/feedback.",
        "tags": "ПВУ приточная установка наружный воздух заслонка привод damper animated airflow модульная секция",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_filter": {
        "name": "ПВУ · Секция фильтров",
        "category": "ПВУ · модульные секции",
        "description": "Модуль корпуса ПВУ с кассетными карманными фильтрами; единые стыковочные фланцы.",
        "tags": "ПВУ фильтр карманный кассетный очистка воздуха filter modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_heat_recovery": {
        "name": "ПВУ · Секция пластинчатого рекуператора",
        "category": "ПВУ · модульные секции",
        "description": "Перекрёстноточный пластинчатый рекуператор в общем корпусе ПВУ.",
        "tags": "ПВУ рекуператор пластинчатый теплоутилизация heat recovery modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_heating_coil": {
        "name": "ПВУ · Секция водяного нагревателя",
        "category": "ПВУ · модульные секции",
        "description": "Водяной калорифер с ламельным пакетом, подачей и обраткой горячего теплоносителя.",
        "tags": "ПВУ нагреватель калорифер водяной горячая вода heating coil modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_cooling_coil": {
        "name": "ПВУ · Секция водяного охладителя",
        "category": "ПВУ · модульные секции",
        "description": "Водяной охладитель с ламельным пакетом, синим контуром холодоносителя и поддоном конденсата.",
        "tags": "ПВУ охладитель охлаждение холодная вода cooling coil modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_supply_fan": {
        "name": "ПВУ · Секция приточного вентилятора",
        "category": "ПВУ · модульные секции",
        "description": "Центробежный вентилятор с электродвигателем; рабочее колесо вращается при BOOL/value=1.",
        "tags": "ПВУ вентилятор приточный центробежный fan motor rotor animated airflow modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
    "ahu_section_open_plenum": {
        "name": "ПВУ · Открытая выходная секция после вентилятора",
        "category": "ПВУ · модульные секции",
        "description": "Пустая выходная секция-удлинитель после вентилятора; боковая облицовка снята, внутренний воздушный канал открыт и виден.",
        "tags": "ПВУ выходной короб пленум plenum открытая секция без боковой стенки airflow modular ahu",
        "visual_style": "isometric-3d-modular-cutaway", "view": "shared-ahU-module"
    },
})


def list_symbols() -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for key, meta in SVG_SYMBOLS.items():
        result.append({
            "id": key, **meta,
            "tags": f"{meta.get('tags', '')} 3D iso3d изометрия объёмный объемный HVAC ИТП Niagara-style",
            "version": "2.0.0",
            "svg_url": f"/api/graphics/library/{key}/svg",
        })
    return result


def read_symbol_svg(symbol_id: str) -> bytes:
    if symbol_id not in SVG_SYMBOLS:
        raise KeyError(symbol_id)
    path = (SVG_DIR / f"{symbol_id}.svg").resolve()
    if path.parent != SVG_DIR.resolve() or not path.is_file():
        raise FileNotFoundError(symbol_id)
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    lowered = text.lower()
    import re
    external_reference = re.search(r"(?:href|src)\s*=\s*['\"]\s*https?://", lowered)
    event_handler = re.search(r"\son[a-z]+\s*=", lowered)
    if ("<script" in lowered or "javascript:" in lowered or "<foreignobject" in lowered
            or external_reference or event_handler or "@import" in lowered):
        raise ValueError(f"Unsafe packaged SVG asset: {symbol_id}")
    return payload
