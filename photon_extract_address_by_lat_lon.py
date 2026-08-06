import os
import time
import requests
import geopandas as gpd


INPUT_PATH = r""
OUTPUT_PATH = r""


# функция для обращения к Photon API (должен быть запущен локально на порту 2322) -> docker load -i photon-1.0.1.tar
# возвращает словарь с адресом и его компонентами (улица, дом, город)
def photon_reverse(lat, lon):
    url = "http://localhost:2322/reverse"

    params = {
        "lat": lat,
        "lon": lon
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        data = r.json()
        features = data.get("features", [])

        if not features:
            return None

        props = features[0]["properties"]

        address = ", ".join(filter(None, [
            props.get("state"),
            props.get("city") or props.get("locality"),
            props.get("street"),
            props.get("housenumber"),
            props.get("name")
        ]))

        return {
            "address": address,
            "addr_housenumber": props.get("housenumber"),
            "addr_street": props.get("street"),
            "addr_city": props.get("city") or props.get("locality"),
        }

    except Exception as e:
        print(f"Photon error: {e}")
        return None



if not os.path.exists(INPUT_PATH):
    raise FileNotFoundError(INPUT_PATH)

gdf = gpd.read_file(INPUT_PATH, driver = 'geojson')


fields = [
    "photon_address",
    "addr_city",
    "addr_street",
    "addr_housenumber"
]

# создаём поля
for field in fields:
    gdf[field] = None

# корректно в 3857
centroids = (
    gdf.to_crs(3857)
       .geometry
       .centroid
       .to_crs(4326)
)



total = len(gdf)
start = time.time()

for i, (idx, centroid) in enumerate(zip(gdf.index, centroids), 1):

    if i % 10000 == 0:
        print(f"{i}/{total}")

    lon = centroid.x
    lat = centroid.y

    result = photon_reverse(lat, lon)

    if result:
        gdf.at[idx, "photon_address"] = result["address"]
        gdf.at[idx, "addr_housenumber"] = result["addr_housenumber"]
        gdf.at[idx, "addr_street"] = result["addr_street"]
        gdf.at[idx, "addr_city"] = result["addr_city"]


gdf.to_file(
    OUTPUT_PATH,
    driver="GPKG",
    layer="addresses"
)

print(f"Сохранено: {OUTPUT_PATH}")