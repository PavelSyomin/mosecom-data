from urllib.request import urlopen

from bs4 import BeautifulSoup


def main():
    STATIONS_LIST_URLS = ["https://ru.wikipedia.org",
                          "https://mosecom.mos.ru/specialnye-stancii/"
                        ]
    BASE_URL = "https://mosecom.mos.ru/"
    STATIONS_FOUT_NAME = "stations.txt"
    PROFILERS_FOUT_NAME = "profilers.txt"
    stations = []

    for station_list_url in STATIONS_LIST_URLS:
        with urlopen(station_list_url) as con:
            data = con.read().decode("utf8")

        if data:
            soup = BeautifulSoup(data, "html.parser")
            stations_list = soup.find("div", id="searching-data")
            if not stations_list:
                continue
            for station_div in stations_list.find_all("div", recursive=False):
                link = station_div.find("a")
                if link:
                    url = link.get("href")
                if not url:
                    print("No URL for station")
                    continue
                station_name = url.replace(BASE_URL, "").strip("/")
                stations.append(station_name)
        else:
            print(f"No data for URL {station_list_url}")

    # Add profilemeters manually, because there are only two of them
    profilers = [
        "vostok",
        "ostankino"
        ]

    with open(STATIONS_FOUT_NAME, "w") as f:
        f.write("\n".join(stations))

    with open(PROFILERS_FOUT_NAME, "w") as f:
        f.write("\n".join(profilers))


if __name__ == "__main__":
    main()
