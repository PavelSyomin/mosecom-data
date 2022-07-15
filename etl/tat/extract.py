import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


url = "http://www.tatarmeteo.ru/ru/monitoring-okruzhayushhej-sredyi/monitoring-zagryazneniya-atmosfernogo-vozduxa-kazani.html"
out_dir = os.path.join("data", "tat", "raw")
timestamp = datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds")

logs_dir = os.path.join("logs", "tat", "extract")
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir)
logging.basicConfig(
    filename=os.path.join(logs_dir, f"extract_{timestamp}.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
)

def main():
    logging.info(f"Trying to get data")
    data = get_raw_data(url)
    if not data:
        logging.warning(f"No data")
        return
    try:
        filename = save_raw_data(data)
        logging.info(f"Data saved to {filename}")
    except:
        logging.error("Cannot save data")

def get_raw_data(url):
    logging.info(f"Trying to get {url}")
    try:
        with urlopen(url) as con:
            html = con.read().decode()
    except HTTPError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"Error code {e.code}: {e.reason}")
        return None
    except URLError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"{e.reason}")
        return None

    logging.info("Data retrieved. Extracting placemarks")
    regex = re.compile("myPlacemark\d{1,2} = ")
    parts = re.split(regex, html)
    placemarks = [part for part in parts if "balloonContent" in part]
    logging.info(f"Detected {len(placemarks)} placemarks")
    data = []
    for placemark in placemarks:
        regex_coords = re.compile("Placemark\(\[(\d{2}\.\d+, ?\d{2}.\d+)\]")
        regex_content = re.compile("balloonContent: ?'([^']+)'")
        placemark_coords = re.search(regex_coords, placemark)
        if placemark_coords:
            coords_str = placemark_coords.group(1)
            coords_str = coords_str.replace(" ", "")
            lat, lon = tuple(map(float, coords_str.split(",")))
        else:
            lat, lon = None, None
            logging.warning("No coords")
        placemark_data = re.search(regex_content, placemark)
        if placemark_data:
            content = placemark_data.group(1)
        else:
            content = None
            logging.warning("No content")

        if content:
            point_data = {
                "coords": {"lat": lat, "lon": lon},
                "content": content
            }
            data.append(point_data)

    return data

def save_raw_data(data):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    filename = os.path.join(out_dir, f"{timestamp}.json")
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    return filename

if __name__ == "__main__":
    main()
