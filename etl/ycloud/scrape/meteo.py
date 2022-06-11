from collections import namedtuple
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.request import urlopen

Meteodata = namedtuple("Meteodata",
    ["datetime", "height", "temperature"])

class MeteoprofileParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._BASE_URL = "https://mosecom.mos.ru/meteo/profilemery/"
        self._data = []

    def handle_starttag(self, tag, attrs):
        if tag != "rect":
            return

        dt, height, temperature = [None] * 3
        for attr in attrs:
            if attr[0] == "data-val":
                try:
                    temperature = float(attr[1])
                except ValueError:
                    pass
            if attr[0] == "data-height":
                height = int(attr[1])
            if attr[0] == "data-date":
                dt = datetime.strptime(attr[1], "%d.%m.%Y %H:%M")
                dt = dt.replace(tzinfo=timezone(timedelta(hours=3)))
                dt = dt.isoformat()
        if dt and height is not None and temperature is not None:
            datarow = Meteodata(dt, height, temperature)
            self._data.append(datarow)

    def parse(self, profiler_name):
        url = self._BASE_URL + profiler_name
        try:
            with urlopen(url) as con:
                html = con.read().decode("utf8")
                self.feed(html)
        except:
            raise RuntimeError(f"Cannot open or parse url {url}")

        return self._data
