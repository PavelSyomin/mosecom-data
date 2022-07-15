import json
import logging
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


base_url = "http://www.feerc.ru/uisem/portal/ad/services/getData.php"
out_dir = os.path.join("data", "feerc", "raw", "history_before_2022-07-15")
timestamp = datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds")

logs_dir = os.path.join("logs", "feerc", "extract")
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir)
logging.basicConfig(
    filename=os.path.join(logs_dir, f"extract_history_before_2022-07-15.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
)

def main():
    start_date = date(2012, 1, 7)
    step = timedelta(days=7)
    end_date = date(2022, 7, 15)
    request_date = start_date
    while request_date < end_date:
        data = get_raw_data(request_date)
        if not data:
            print(f"No data for {request_date.strftime('%d.%m.%Y')}")
            continue
        try:
            save_raw_data(data, request_date)
        except BaseException as e:
            logging.critical("Cannot save data")
            logging.critical(str(e))
        request_date += step

def get_raw_data(request_date):
    request_date = request_date.strftime("%d.%m.%Y")
    logging.info(f"Trying to get data on {request_date}")
    params = {
        "d": request_date,
        "t": "ntag"
    }
    params_str = urlencode(params)
    url = f"{base_url}?{params_str}"
    try:
        with urlopen(url) as con:
            response = con.read().decode()
    except HTTPError as e:
        logging.error(f"Cannot get data from {url}")
        logging.error(f"Error code {e.code}: {e.reason}")
        return None
    except URLError as e:
        logging.error(f"Cannot get data from {url}")
        logging.error(f"{e.reason}")
        return None

    try:
        response = json.loads(response)
    except:
        logging.error("Cannot load JSON data")
        return None

    if not response:
        logging.error("No data")
        return None

    data = {}
    status = response.get("status", 0)
    if status != 1:
        logging.warning("Status of response is not equal to 1")
    data["status"] = status
    resp_date = response.get("date")
    if resp_date and resp_date != request_date:
        logging.warning("Date in response is not equal to date in request: "
                        + f"Request: {request_date} != response: {resp_date}")
    data["date"] = resp_date
    count = Counter()
    data["data"] = []
    for i, group in enumerate(response.get("data", [])):
        gtype = group.get("type")
        stations = []
        for j, station in enumerate(group.get("stations", [])):
            pollution_history = station.get("primsSS", [])
            if len(pollution_history) == 0:
                continue
            st_name = station.get("name", "").split("(")[0]
            count.update([st_name])
            stations.append(station)
        if len(stations) > 0:
            data["data"].append({"type": gtype, "stations": stations})
    counts_str = "; ".join([f"{city} — {n}"
                            for city, n in sorted(count.items())])
    logging.info(f"Extracted data for stations in cities: {counts_str}")

    sleep(5)
    return data

def save_raw_data(data, request_date):
    if not data:
        return
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    file_date = request_date.isoformat()
    filename = os.path.join(out_dir, f"{file_date}.json")
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    logging.info(f"Data saved to {filename}")

if __name__ == "__main__":
    main()
