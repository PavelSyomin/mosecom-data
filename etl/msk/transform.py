import csv
import logging
from datetime import datetime, timedelta, timezone
import json
import os
from collections import namedtuple


Params = namedtuple("Params", [
    "raw_data_dir",
    "product_dir",
    "logs_dir",
    "current_dt"
])

params = Params(
    raw_data_dir="data/msk/raw",
    product_dir="data/msk/product",
    logs_dir=os.path.join("logs", "msk", "transform"),
    current_dt=datetime.now(tz=timezone(timedelta(hours=3)))\
            .isoformat(timespec="seconds"),
)

HEADERS = {
    "stations": ("datetime", "pollutant", "concentration"),
    "special_stations": ("datetime", "pollutant", "concentration"),
    "profilers": ("datetime", "height", "temperature")
}

if not os.path.isdir(params.logs_dir):
    os.makedirs(params.logs_dir)

logging.basicConfig(
    filename=os.path.join(params.logs_dir, f"transform_{params.current_dt}.txt"),
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG
)

for dirname, _, filenames in os.walk(params.raw_data_dir):
    parts = dirname.split("/")
    if len(parts) != 4:
        continue

    ptype = parts[-2]
    pname = parts[-1]

    out_dir = os.path.join(params.product_dir, ptype, pname)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    if ptype in ("stations", "special_stations"):
        dtypes = ("hourly", "daily", "monthly")
    else:
        dtypes = ("every_5_minutes",)

    for dtype in dtypes:
        out_file = os.path.join(out_dir, f"rolling_{dtype}.csv")
        if os.path.isfile(out_file):
            with open(out_file) as f:
                reader = csv.reader(f)
                max_dt = datetime(1970, 1, 1, 0, 0, 1,
                                  tzinfo=timezone(timedelta(hours=3)))
                for i, line in enumerate(reader):
                    if i == 0:
                        continue
                    dt = datetime.fromisoformat(line[0])
                    if dt > max_dt:
                        max_dt = dt

            rows = set()
            for filename in sorted(filenames):
                file_dt = datetime.fromisoformat(filename\
                                                .rstrip(".json")\
                                                .split("_", maxsplit=1)[1])
                if file_dt < max_dt:
                    continue

                with open(os.path.join(dirname, filename)) as f:
                    json_data = json.load(f)
                data = json_data.get("data")
                if ptype != "profilers":
                    data = data.get(dtype)
                if not data:
                    continue
                for row in data:
                    row = tuple(row)
                    if row[0] is not None:
                        row_dt = datetime.fromisoformat(row[0])
                    else:
                        continue
                    if row_dt > max_dt:
                        rows.add(row)

            with open(out_file, "a") as f:
                writer = csv.writer(f)
                rows = list(rows)
                if ptype == "profilers":
                    rows.sort(key=lambda x: (x[0], x[1] or 0))
                else:
                    rows.sort(key=lambda x: x[0])
                writer.writerows(rows)

        else:
            rows = set()
            for filename in filenames:
                with open(os.path.join(dirname, filename)) as f:
                    json_data = json.load(f)
                data = json_data.get("data")
                if ptype != "profilers":
                    data = data.get(dtype)
                if not data:
                    continue
                for row in data:
                    row = tuple(row)
                    if row[0] is not None:
                        row_dt = datetime.fromisoformat(row[0])
                    else:
                        continue
                    rows.add(row)

            with open(out_file, "w", encoding="utf8") as f:
                writer = csv.writer(f)
                header = HEADERS[ptype]
                writer.writerow(header)
                rows = list(rows)
                if ptype == "profilers":
                    rows.sort(key=lambda x: (x[0], x[1] or 0))
                else:
                    rows.sort(key=lambda x: x[0])
                writer.writerows(rows)

    logging.info(f"Processed {ptype[:-1]} {pname}")

