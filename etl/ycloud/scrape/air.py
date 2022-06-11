import re
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from json import loads
from urllib.request import urlopen


PollutionData = namedtuple("PollutionData",
    ["datetime", "pollutant", "value"])

class PollutionParser:
    def __init__(self):
        self._BASE_URL = "https://mosecom.mos.ru/"
        self._MTYPE_MAPPING = {
            "h": "hourly",
            "w": "daily",
            "m": "daily",
            "y": "monthly"
        }
        self._data = {}

    def parse(self, point_name):
        url = self._BASE_URL + point_name
        try:
            with urlopen(url, timeout=30) as con:
                html = con.read().decode("utf8")
        except:
            raise RuntimeError(f"Cannot open url {url}")

        script = re.findall("AirCharts.init.*", html)[0]
        data_start = len("AirCharts.init(")
        data_end = script.find(', {"months"')
        data = loads(script[data_start:data_end])

        for mtype, measurements in data["units"].items():
            if mtype not in self._MTYPE_MAPPING:
                continue
            if mtype == "w" and "m" in data["units"]:
                continue
                # w and m are generally the same, so we need only one of them
            self._data.setdefault(self._MTYPE_MAPPING[mtype], [])
            for pollutant, pollutant_data in measurements.items():
                for ts, value in pollutant_data["data"]:
                    dt = datetime.utcfromtimestamp(ts // 1000)
                    dt = dt.replace(tzinfo=timezone(timedelta(hours=3)))
                    dt = dt.isoformat()
                    row = PollutionData(dt, pollutant, value)
                    self._data[self._MTYPE_MAPPING[mtype]].append(row)

        if len(self._data) == 0:
            raise RuntimeError(f"No data for profiler {point_name}")

        return self._data
