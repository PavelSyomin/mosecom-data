import json
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen


url = "http://www.pogoda-sv.ru/pollcenter/airdata/api/get_station_meas_last_list"
out_dir = os.path.join("data", "volga", "raw")
timestamp = datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds")

logs_dir = os.path.join("logs", "volga", "extract")
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
        data = json.loads(content)
        logging.info(f"Extracted data from {len(data)} points")
    except:
        logging.error("Data is missing or corrupted")
        return None

    return data

def save_raw_data(data):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    filename = os.path.join(out_dir, f"{timestamp}.json")
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False)

if __name__ == "__main__":
    main()
