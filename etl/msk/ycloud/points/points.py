from json import dumps
from urllib.request import urlopen

from bs4 import BeautifulSoup


def parse():
    INFO_URLS = {
        "stations": "https://mosecom.mos.ru/stations/",
        "special_stations": "https://mosecom.mos.ru/specialnye-stancii/"
    }
    BASE_URL = "https://mosecom.mos.ru/"
    data = {
        "stations": [],
        "special_stations": [],
        "profilers": [
            "vostok",
            "ostankino"
        ] # added manually, because there are only 2 profilers
    }

    for point_type, url in INFO_URLS.items():
        try:
            with urlopen(url) as con:
                html = con.read().decode("utf8")
        except:
            continue

        soup = BeautifulSoup(html, "html.parser")
        stations_list = soup.find("div", id="searching-data")
        for station_div in stations_list.find_all("div", recursive=False):
            link = station_div.find("a")
            if link:
                url = link.get("href")
            if not url:
                continue
            station_name = url.replace(BASE_URL, "").strip("/")
            data[point_type].append(station_name)

    return data


def main(event, context):
    data = parse()
    if len(data["stations"]) == 0 or len(data["special_stations"]) == 0:
        code = 500
        status = "Error"
    else:
        code = 200
        status = "OK"
    result = {
        "status": status,
        "data": data
    }

    return {
        'statusCode': code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'isBase64Encoded': False,
        'body': dumps(result)
    }
