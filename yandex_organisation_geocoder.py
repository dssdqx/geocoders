import json
import requests



def search_organization(query: str, api_key: str) -> dict:
    """Ищет организацию через API Поиска по организациям (Places API)."""
    base_url = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": api_key,
        "text": query,
        "type": "biz",
        "lang": "ru_RU",
        "results": 1
    }

    try:
        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Ошибка запроса:", e)
        return None

    try:
        features = data.get("features", [])
        if not features:
            return None

        first_match = features[0]
        coords = first_match["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        
        props = first_match.get("properties", {})
        company_meta = props.get("CompanyMetaData", {})

        address_data = company_meta.get("address")
        if isinstance(address_data, dict):
            formatted_address = address_data.get("formatted")
        else:
            formatted_address = address_data

        org_name = company_meta.get("name")
        categories = [cat.get("name") for cat in company_meta.get("Categories", [])]
        category_str = ", ".join(categories) if categories else None

        return {
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "formatted_address": formatted_address,
            "name": org_name,
            "category": category_str
        }
    except (KeyError, IndexError, ValueError) as e:
        print("Ошибка парсинга ответа:", e)
        return None