import json
import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


base_url = "http://www.feerc.ru/uisem/portal/ad/services/getData.php"
out_dir = os.path.join("data", "feerc", "raw")
timestamp = datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds")

logs_dir = os.path.join("logs", "feerc", "extract")
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir)
logging.basicConfig(
    filename=os.path.join(logs_dir, f"extract_{timestamp}.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
)

def main():
    data = get_raw_data()
    if not data:
        return
    try:
        save_raw_data(data)
    except BaseException as e:
        logging.critical("Cannot save data")
        logging.critical(str(e))

def get_raw_data():
    params = {
        "d": "now",
        "t": "ntag"
    }
    params_str = urlencode(params)
    url = f"{base_url}?{params_str}"
    try:
        with urlopen(url) as con:
            content = con.read().decode()
    except HTTPError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"Error code {e.code}: {e.reason}")
        return None
    except URLError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"{e.reason}")
        return None

    try:
        response = json.loads(content)
    except:
        logging.error("Cannot load JSON data")
        return None

    if response:
        status = response.get("status", 0)
        if status != 1:
            logging.warning("Status of response is not equal to 1")
        data = response.get("data", [])
        stations = []
        for group in data:
            for station in group.get("stations", ""):
                st_name = station.get("name", "").split("(")[0]
                stations.append(st_name)
        counts = Counter(stations)
        counts_str = "; ".join([f"{city} — {n}"
                                for city, n in sorted(counts.items())])
        logging.info(f"Extracted data for stations in cities: {counts_str}")

    return response

def save_raw_data(data):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    filename = os.path.join(out_dir, f"{timestamp}.json")
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    logging.info(f"Data saved to {filename}")

if __name__ == "__main__":
    main()
