import os
from datetime import date
from time import sleep
from urllib.request import urlopen, Request
from urllib.parse import urlencode

from bs4 import BeautifulSoup


out_dir = os.path.join("data", "spb", "raw", "asmav", "history_before_2022-07-04")
base_url = "http://www.infoeco.ru"
year_ids = {
    2017: 3122,
    2018: 4355,
    2019: 6532,
    2020: 8221,
    2021: 10547,
    2022: 14797
}

def main():
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    stats = {}
    for year, year_id in year_ids.items():
        stats[year] = {"ok": 0, "error": 0}
        print(f"Gathering data for year {year}")
        params = urlencode({"id": year_id})
        url = f"{base_url}/index.php?{params}"
        links = []

        soup = get_soup(url)
        if not soup:
            continue
        pagination = soup.find(id="pagination")
        pages = [a.attrs.get("href") for a in pagination("a")]
        print(f"Pages count: {len(pages) + 1}")

        print("Processing page #1")
        links.extend(get_links_from_soup(soup))
        for i, page in enumerate(pages):
            print(f"Processing page {i+2}")
            url = f"{base_url}{page}"
            soup = get_soup(url)
            if not soup:
                continue
            links.extend(get_links_from_soup(soup))

        print(f"Found {len(links)} links for year {year}")

        for link in links:
            res = process_link(link)
            if res == 0:
                stats[year]["ok"] += 1
            else:
                stats[year]["error"] += 1

    print("All years processed with the following results:")
    for year, results in stats.items():
        print(f"{year}: {results['ok']} OK, {results['error']} errors")
    print("Data files saved to {out_dir}")


def get_soup(url):
    try:
        with urlopen(url) as con:
            html = con.read().decode()
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"Cannot get data from {url}")
        print(e)
        soup = None

    sleep(1)

    return soup


def get_links_from_soup(soup):
    section = soup.find("section")
    articles = section("article")
    res = []
    for article in articles:
        link = article.find("a").attrs.get("href").lstrip("/")
        res.append(link)

    print(f"Found {len(res)} links on page")
    return res


def process_link(link):
    print(f"Processing {link}")
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"}
    url = f"{base_url}/{link}"
    req = Request(url=url, headers=headers)
    try:
        with urlopen(req) as con:
            data = con.read()
            ctype = con.info().get_content_type()
    except Exception as e:
        print("Cannot get data from requested url")
        print(e)
        return 1

    if ctype == "text/html":
        out_format = "html"
    elif ctype == "application/msword":
        out_format = "doc"
    elif ctype.startswith("application/vnd.openxmlformats"):
        out_format = "docx"
    else:
        print("Unrecognized content type")
        return 1

    id_ = url.rsplit("=", maxsplit=1)[1]
    filename = f"asmav_all_{id_}.{out_format}"
    with open(os.path.join(out_dir, filename), "wb") as f:
        f.write(data)

    sleep(1)

    return 0


if __name__ == "__main__":
    main()
