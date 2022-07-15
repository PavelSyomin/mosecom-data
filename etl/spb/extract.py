import gzip
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, parse_qs, urlencode, urlparse
from urllib.request import urlopen, Request


base_url = "https://www.mineral.spb.ru/"
script_url = "http://www.infoeco.ru/assets/files/air/placemark.js"
out_dir = os.path.join("data", "spb", "raw")
timestamp = datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds")
logs_dir = os.path.join("logs", "spb", "extract")
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir)

logging.basicConfig(
    filename=os.path.join(logs_dir, f"extract_{timestamp}.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
)

def main():
    station_ids = get_station_ids(script_url)

    stats = {"ok": 0, "error": 0}
    for stype, sids in station_ids.items():
        for sid in sorted(sids):
            res = get_data_for_station(stype, sid)
            if res == 0:
                stats["ok"] += 1
            else:
                stats["error"] += 1

    logging.info(f"Extracted data for {timestamp}")
    logging.info(f"{stats['ok']} stations were processed successfuly "
        + f"{stats['error']} with errors")


def get_station_ids(url):
    logging.info("Getting station ids")
    SKIP_IDS = {
        "asmav": [],
        "gmsav": [5] # Station with id 5 do not work
    }
    res = {
        "asmav": set(),
        "gmsav": set()
    }
    try:
        with urlopen(url) as con:
            src = con.read()
    except HTTPError as e:
        logging.critical("Cannot get data about stations")
        logging.critical(f"Error code {e.code}: {e.reason}")
        return res
    except URLError as e:
        logging.critical("Cannot get data about stations")
        logging.critical(f"{e.reason}")
        return res

    src = src.decode("windows-1251")

    regex = re.compile("<iframe[^>]+ src=([^ ]+)>")
    for match in regex.finditer(src):
        link = match.group(1)
        stype = "asmav" if "asmav" in link else "gmsav"
        query = urlparse(link).query
        ids_arg = parse_qs(query).get("id")
        if len(ids_arg) == 1:
            id_ = ids_arg[0]
        else:
            logging.warning("Unexpected number of ids")
        try:
            id_ = int(id_)
        except ValueError:
            logging.warning("Id is not numeric")
            continue
        if id_ in SKIP_IDS[stype]:
            continue

        res[stype].add(id_)

    log_str = ", ".join(
        [f"{len(values)} {key} stations" for key, values in res.items()]
    )
    logging.info(f"Obtained results: {log_str}")

    return res


def get_data_for_station(stype, sid):
    logging.info(f"Processing {stype} station with id {sid}")
    url = f"{base_url}{stype}30d/index.php?id={sid}"
    try:
        with urlopen(url) as con:
            html = con.read().decode("windows-1251")
    except HTTPError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"Error code {e.code}: {e.reason}")
        return 1
    except URLError as e:
        logging.critical(f"Cannot get data from {url}")
        logging.critical(f"{e.reason}")
        return 1
    except ValueError as e:
        logging.critical(f"Cannot decode data from {url}")
        return 1

    regex = re.compile("<img[^>]+src=([^ ]+)")
    images_src = []
    for match in regex.finditer(html):
        src = match.group(1)
        src = src.strip("'\"")
        images_src.append(src)

    if len(images_src) != 2:
        logging.warning("Unexpected number of images")

    images = []
    for src in images_src:
        image_url = urljoin(url, src)
        try:
            with urlopen(image_url) as con:
                data = con.read()
        except Exception:
            logging.error(f"Cannot get image {url}")
            continue
        images.append(data)

    out_path = os.path.join(out_dir, stype, str(sid), timestamp)
    if not os.path.isdir(out_path):
        os.makedirs(out_path)

    html = html.replace("charset=windows-1251", "charset=utf8")
    html_filename = os.path.join(out_path, "index.html")
    with open(html_filename, "w") as f:
        f.write(html)

    for i, image in enumerate(images):
        img_filename = os.path.join(out_path, f"image_{i}.gif")
        with open(img_filename, "wb") as f:
            f.write(image)

    sleep(1)
    return 0


if __name__ == "__main__":
    main()
