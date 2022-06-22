import argparse
import logging
from collections import namedtuple
from json import load, loads, dump
from datetime import datetime, timedelta, timezone
from os import makedirs
from os.path import isdir, join
from time import sleep
from urllib.request import Request, urlopen


Params = namedtuple("Params", [
                    "points_url",
                    "scrape_url",
                    "base_dir",
                    "logs_dir",
                    "points_filename",
                    "current_dt"])

params = Params(
    points_url="https://functions.yandexcloud.net/d4erfpvs3mpost7o71j6",
    scrape_url="https://functions.yandexcloud.net/d4eap6qup80439vvjltc",
    base_dir=join("data", "raw"),
    logs_dir=join("logs", "extract"),
    points_filename="points.json",
    current_dt=datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds"),
    )

if not isdir(params.logs_dir):
    makedirs(params.logs_dir)

logging.basicConfig(
    filename=join(params.logs_dir, f"extract_{params.current_dt}.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
    )

parser = argparse.ArgumentParser(description="Extract data from Mosecom.mos.ru")
parser.add_argument("--apikey",
    type=str,
    help="API key to call cloud function on Yandex Cloud",
    required=True
    )
args = parser.parse_args()


def main():
    points = get_points()
    if not points:
        points = load_previous_points()
    else:
        save_points(points)

    if not points:
        logging.critical("Cannot extract points "
            + "or load them from a file. Execution stopped")
        return

    counts = {}
    for ptype, pnames in points.items():
        for pname in pnames:
            res = extract_data(ptype, pname)
            if res == 0:
                counts.setdefault(ptype, 0)
                counts[ptype] += 1

    logging.info(f"Extracted data: {counts}")


def get_points() -> dict:
    req = Request(
        url=params.points_url,
        headers={
            "Authorization": f"Api-Key {args.apikey}"
            }
        )
    try:
        with urlopen(req) as con:
            response = con.read().decode("utf8")
            response = loads(response)
    except:
        logging.error(f"Cannot extract points")
        return None

    if response["status"] != "OK":
        logging.warning("Probably incorrect data: status is not OK")
        return None

    counts = {
        ptype: len(pnames)
        for ptype, pnames
        in response["data"].items()
        }
    logging.info(f"Points extracted: {counts}")

    return response["data"]


def save_points(points: dict):
    if not isdir(params.base_dir):
        makedirs(params.base_dir)

    filename = join(params.base_dir, params.points_filename)
    with open(filename, "w") as f:
        try:
            dump(points, f)
            logging.info(f"Points saved to {filename}")
        except:
            logging.error(f"Cannnot save points")


def load_previous_points() -> dict:
    filename = join(params.base_dir, params.points_filename)
    try:
        with open(filename) as f:
            points = load(f)
            logging.info(f"Loaded previous version of points from {filename}")
            return points
    except:
        logging.error(f"Cannot load previous version of points")
        return None


def extract_data(ptype: str, pname: str) -> int:
    ptype_url_arg = ptype.rstrip("s")
    ptype_print = ptype.replace("_", " ")
    url = params.scrape_url + f"?point={pname}&type={ptype_url_arg}"
    req = Request(
        url=url,
        headers={
            "Authorization": f"Api-Key {args.apikey}"
        }
    )

    try:
        with urlopen(req) as con:
            response = con.read().decode()
            data = loads(response)
            logging.info(f"Extracted data for {pname} {ptype_print}")
    except:
        logging.error(f"Cannot extract data for {pname} {ptype_print}")
        return 1

    if data["status"] == "OK":
        path = join(params.base_dir, ptype, pname)
        if not isdir(path):
            makedirs(path)
        filename = join(path, f"{pname}_{params.current_dt}.json")
        del data["status"]

        try:
            with open(filename, "w") as f:
                dump(data, f)
                logging.info(f"Data for {pname} {ptype_print} saved to {filename}")
        except:
            logging.error(f"Cannot save data for {pname} {ptype_print} saved to "
                + f"{filename}")
            return 1
    else:
        logging.error(f"Incorrect data for {pname} {ptype_print}"
            + f"data['message']")

    return 0


if __name__ == "__main__":
    main()
