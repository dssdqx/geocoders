import os 
import geopandas as gpd
from pynspd import Nspd, NspdFeature
from shapely import Point
from pathlib import Path
import json

# ---------- загрузка данных ----------

input_file = Path(r"c:\maps\2gis_справочник\11-2025\stavropol_tourism_2gis_formatted.geojson")
output_file = input_file.with_stem(f"{input_file.stem}_nspd_info")


gdf = gpd.read_file(input_file)
total = len(gdf)

nspd = Nspd(
    client_timeout=20,
    client_retries=5,
    cache_folder_path=r"c:\maps\geocoder\nspd_cache",
    cache_ttl=None
)

#layer_building = NspdFeature.by_title("Здания")
layer_zus = NspdFeature.by_title("Земельные участки из ЕГРН") # СЛОЙ ГДЕ ИЩЕМ УЧАСТОК ПО ТОЧКЕ

# ---------- функция для получения кадастрового номера и всей информации по участку ----------

def geocoder(lat, lon, layer):
    pt = Point(lon, lat)
    feats = nspd.search_at_point(pt, layer)

    if not feats:
        return None, None

    opts = feats[0].properties.options
    data = opts.dict()

    cad_num = data.get("cad_num")

    cad_info_json = json.dumps(
        data,
        ensure_ascii=False,
        default=str  # datetime → строка
    )
    return cad_num, cad_info_json



cad_nums = []
cad_infos = []
# ---------- перебор точек ----------
for idx, row in gdf.iterrows():
    lat = row['lat']
    lon = row['lon']
    print(f"[{idx+1}/{total}] lat={lat}, lon={lon}")
    
    cad_num, cad_info = geocoder(lat, lon, layer_zus)
    cad_nums.append(cad_num)
    cad_infos.append(cad_info)
    
    print(f"Кадастровый номер: {cad_num}")
    print(f"Вся информация: {cad_info}\n")

# ---------- добавление столбцов в GeoDataFrame ----------
gdf['cad_num'] = cad_nums
gdf['cad_info'] = cad_infos

# ---------- сохранение в GeoJSON ----------
gdf.to_file(output_file,driver="GeoJSON")
print(f"Готово! Результат сохранён в {output_file}")
