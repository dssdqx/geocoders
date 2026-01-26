import requests
import pandas as pd
from pathlib import Path
import time

API_KEY = ""

input_file = Path(r'c:\maps\input.csv')
output_file = input_file.parent / 'export_xy_yandex.csv'

df = pd.read_csv(input_file, sep=";", encoding="utf-8")
df.columns = df.columns.str.lower() 


df["lat_yandex"] = 0.0
df["lon_yandex"] = 0.0
df["address_yandex"] = None
df["object_name_yandex"] = None # вернёт улицу\дом, конечный объект
df["precision_yandex"] = None  # точность определения exact, number, street, near, other, range


def check_connection():   
    #Проверяет подключение к Яндекс Геокодеру.
    try:
        r = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={"apikey": API_KEY, "geocode": "Москва, Кремль", "format": "json"},
            timeout=5
        )
        r.raise_for_status()
        data = r.json()
        if "response" in data:
            print("Подключение успешно к geocode-maps.yandex.ru ")
            return True
    except Exception as e:
        print("Ошибка подключения или превышен лимит запросов (1000 в день)", e)
        return False


def geocode_address(address: str) -> dict:
    """
    Геокодирует адрес через Яндекс HTTP Геокодер.
    Возвращает словарь: {lat, lon, formatted_address}
    """
    base_url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": API_KEY,
        "geocode": address,
        "format": "json",
        "lang": "ru_RU",
        "results": 1
    }

    try:
        response = requests.get(base_url, params=params, timeout=5)
        data = response.json()
    except Exception as e:
        print("Ошибка запроса:", e)
        return None

    try:
        feature_member = data["response"]["GeoObjectCollection"]["featureMember"]
        if not feature_member:
            return None

        geo_obj = feature_member[0]["GeoObject"]
        pos = geo_obj["Point"]["pos"]  # формат: "lon lat"
        lon, lat = map(float, pos.split())
        formatted_address = geo_obj["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"]
        name = geo_obj.get("name")
        precision = geo_obj["metaDataProperty"]["GeocoderMetaData"].get("precision")

        return {
            "lat": lat,
            "lon": lon,
            "formatted_address": formatted_address,
            "name": name,
            "precision": precision
        }
    except (KeyError, IndexError, ValueError):
        return None

total = len(df)
not_found_count = 0
processed = 0


if not check_connection():
    exit(1)


for idx, row in df.iterrows():
    processed += 1
    address = str(row["address"])  #передаём адрес из колонки address

    if not address or address.lower() == "nan":   # не будет запросов к API на пустоту, не будет мусорных координат
        not_found_count += 1
        print(f"[{processed}/{total}] EMPTY ADDRESS")
        continue

    result = geocode_address(address)

    if result:
        df.at[idx, "lat_yandex"] = round(result["lat"], 6)
        df.at[idx, "lon_yandex"] = round(result["lon"], 6)
        df.at[idx, "address_yandex"] = result["formatted_address"]

        df.at[idx, "object_name_yandex"] = result.get("name")
        df.at[idx, "precision_yandex"] = result.get("precision")
        print(f"[{processed}/{total}] OK: {address} → {result['formatted_address']} (prec={result['precision']})")

    else:
        not_found_count += 1
        print(f"[{processed}/{total}] NOT FOUND: {address}")

    time.sleep(0.25)  # 4 запроса в секунду

df.to_csv(output_file, sep=";", index=False, encoding="utf-8")
print("\nСохранено:", output_file)

print(f"Не найдено: {not_found_count} из {total} ({not_found_count / total:.1%})")
