import os 
import geopandas as gpd
from pynspd import Nspd, NspdFeature
from shapely import Point
from pathlib import Path
import json
import dateparser
import datetime, time


input_file = Path(r"")
output_file = input_file.with_stem(f"{input_file.stem}_nspd_info")


gdf = gpd.read_file(input_file)
total = len(gdf)
print(f"Всего объектов в исходном файле: {total}")


fields_from_nspd = {
    "cad_num": "Кадастровый номер",
    "readable_address": "Адрес",
    "status": "Статус",
    "land_record_category_type": "Категория земель",
    "permitted_use_established_by_document": "Назначение",
    "ownership_type": "Собственность",
    "cost_value": "Кадастровая стоимость",
    "determination_couse": "Основание оценки",
    "land_record_subtype": "Подкатегория землепользования",
    "land_record_reg_date": "Дата постановки на учёт"
}



nspd = Nspd(
    client_timeout=30,
    client_retries=5
)
layer_zus = NspdFeature.by_title("Земельные участки из ЕГРН")


def nspd_parser(pt: Point):
    feats = nspd.search_at_point(pt, layer_zus)
    
    if not feats:
        return None
        
    data = feats[0].properties.options.model_dump()
    
    # 1. Собираем только нужные поля (где ключи совпадают с fields_from_nspd)
    parsed_result = {}
    for key in fields_from_nspd.keys():
        value = data.get(key)
        
        # 1. Если это строка, убираем переносы строк \n и лишние пробелы
        if isinstance(value, str):
            value = value.strip()
        
        #2. Обработка даты в объект datetime
        if key == "land_record_reg_date" and value is not None:
            if isinstance(value, datetime.datetime):
                parsed_date = value
            else:
                # dateparser.parse возвращает готовый объект datetime.datetime
                parsed_date = dateparser.parse(str(value))
            
            value = parsed_date  # Оставляем объект datetime! (или None, если распарсить не удалось)
        parsed_result[key] = value

    return parsed_result




for key in fields_from_nspd.keys():
    gdf[key] = None

q = 0

for idx, row in gdf.iterrows():
    geom = row.geometry
    

    result = nspd_parser(geom)
    time.sleep(0.3)
    
    # Если данные нашлись, записываем их в соответствующие колонки строки `idx`
    if result:
        q+=1
        for key, value in result.items():
            #print(f"idx={idx}, key={key}, value={value}")
            gdf.loc[idx, key] = value
            
    print(f"Обработано объектов: {idx + 1}/{total}")



gdf.to_file(output_file, driver="GeoJSON")
print(f"Готово! Результат сохранен в: {output_file}")
print(f"Количество объектов, для которых найдены данные в NSPD: {q}/{total}")