# Air pollution and meteo data for Russian cities

The goal of this project is to collect data on air pollution in various Russian cities, to store it and to build ready-to-use, convinient and well-documented datasets about air pollution. Also, if it's possible, data on meteorological characteristics is also collected, stored and transformed to datasets. I started this project on my own because it's quiet an interesting technical task for me and because the availability of urban air pollution data in Russia disappoints me: there is no official dataset with long-term frequent records of concentrations of different pollutants in the air as measured by stationary ground monitoring stations, and the absence of such a dataset limits research, education, data journalism, public control and so on.

The project is in a development phase, so few data is avaialble, and coverage is small. However, I hope I will have enough time, skills and enthusiasm to continue working on it (or maybe someone will collab with me :)

## General Approach

Air pollution in Russian cities is measured by state monitoring stations. These stations are stationary (i.e. their location is fixed) and ground (i.e. they are are built on the ground level, and not somewhere on the roofs). Each station performs frequent measurements of concentration of various pollutants (e.g. sulphur dioxide, nitrogen oxide, particulate matter etc), and the frequency of these measurements is about 1 in 20 minutes or 1 in a hour. In general, this data is not made available to public. The typical way of disclosing information about air pollution measured by these stations is to publish daily, weekly or monthly reports containing information about only a limited number of measurements, that is, cases when the average level of pollution for a considerably long time has become larger than the maximum allowable concentration level. Also, sometimes quick warnings are issued with information that the registered level of some pollutant is much more than allowed maximum. Despite the fact such reports and warnings are useful in some situations, they are inconvenient and insufficient if one tries to perform any kind of statistical or spatial analysis or visualization, because data is not provided in machine-readible format and is very sparse in terms of time and space resolution (only facts about *some* stations in *some* days are published).

However, besides this common framework, sometimes it is possible to find data which is full and frequently updated. For some cities there are public maps or plots where the stations are drawn and the results of recent mesaurements are shown. The amount of information available here also varies: sometimes we can see hourly averages of concentrations of various pollutants, and sometimes only daily averages are shown, and the number of pollutants for which the data is available is different. Also, there is no regularity in the presence or absence of information for a particular cities: for some small cities there may be such a map or plot, while for a bigger city there is no public resource. In spite of this, these maps or plots show quiet a detailed information, and often it's possible to capture it, store and then parse and transform to a dataset. This capturing, storing, parsing and dataset formation is the main objective of scripts in this repository.

Sometimes these air pollution portals also display information about meteorological characteristics, e.g. temperature, air pressure, wind speed. If it's possible and not very difficult, it's also stored.

## Current Implementation

At this point, there are scripts for two largets cities: Moscow and Saint Petersburg.

### Overall structure

The general workflow is as follows.

1. Get data from a website for particular city or cities.
2. Save it in `data` folder.
3. Parse downloaded data and save the results in a CSV file containing information about concentration of pollutants with a timestamp.
4. Repeat with some interval depending on the frequency of updates of the target website and the length of the history preserved between the updates.

### Files and Folders Description

* `etl` — scripts for processing data:
  - `extract.py` — scripts for retrieving “raw” data from websites;
  - `transform.py` — scripts for parsing and building CSVs.
* `data` — stored data:
  - `raw` — data in format it was extracted (`html`, `doc`, `docx`, sometimes `json`);
  - `product` — CSV files.
* `logs` — log files;
* `.github/workflows` — configuration files of workflows on GitHub Actions used for automation.

## City-Specific Notes

### Moscow

1. Data is gathered from http://mosecom.mos.ru
2. The website blocks requests from GitHub IPs, probably because they are foreign, so to retrieve data, two helper Yandex Cloud functions are used as a gateway. The code of these functions is in `etl/msk/ycloud` folder.
3. There are three types of points:
    * stations,
    * special stations — something like ordinary stations, but located in heavy polluted places (at least as far as I understand),
    * profilers — meteorological tools used to measure air temperature on different height. This data may sometimes help in solving some tasks related to air pollution, e.g. inversion of temperature is related to greater level of pollution, and thus temperature profile may be helpful in pollution prediction tasks.
4. Raw data includes:
    - list of all points (just short codes used as parts of page URLs);
    - JSON files with timestamp, pollutant code and value (for stations and special stations) or with timestamp, height and temperature (for profilers).
5. Product at the point is “rolling” dataset with all measures in “long” format. “Rolling” means that new rows are appended to the end of the existing table, and “long” format contains few columns but a lot of rows. There are three columns in datasets for stations and special stations: datetime, pollutant and value. Datetime is in ISO format, pollutant is a code (e.g. CO, SO2, PM10), value is concentration in mg/m^3. Profilers dataframes also consist of three columns: datetime, height (in meters), and temperature (in Celcius).
6. There are three subtypes of pollution data:
    - hourly averages (`hourly` key in JSON and `hourly` suffix in filenames of “rolling” datasets);
    - daily averages (`daily` key and suffix);
    - monthly averages (`monthly` key and suffix).
7. Data is extracted from the website every day at 23:00 UTC. It's more frequently than needed because even the hourly data in the website persists for 2 days. However, for me it seems that daily updates act as a safeguard from potential problems with the website.

### Saint Petersburg

1. Website is http://infoeco.ru Requests are performed directly from GitHub because there is no blocking.
2. The list of stations is extracted from the script with URL http://www.infoeco.ru/assets/files/air/placemark.js This script is used to display an interactive map and it contains the coordinates and data URLs for each station. The corresponding data is retrieved from respective data URLs which have a format https://www.mineral.spb.ru/<station_type>30d/index.php?id=<station_id>
3. There is historical daily data located at http://www.infoeco.ru/index.php?id=15628 It has been scraped and stored in `data/spb/asmav/history_before_2022-07-04`.
4. There are two types of stations:
    - asmav — stations operated by city's ecological committee (there are 25 of them now);
    - gmsav — stations operated by federal environmental monitoring service (there are about 10 of them).
5. The data is presented as GIF plots ¯\_(ツ)_/¯ So now is's just stored as pictures, but I hope one day it will be digitized.
6. Data transformation — TBD.

### Tatarstan

1. Website is http://www.tatarmeteo.ru/ru/monitoring-okruzhayushhej-sredyi/
2. There is a map with monitoring stations in 4 cities: Kazan (10 stations), Naberezhniye Chelny (5 stations), Almetievsk (3 stations), Nizhnekamsk (3 stations). For each city, there is a separate page on the site, but the map is common, so the data is extracted only once from the map on kazan page.
3. Raw data is stored in `data/tat/raw` as JSON with coordinates and daily averages table for each monitoring station. The city name is not detected, but can be found out later by coordinates.
4. Workflow to extract data is run every day at 22:30.

### Volga region

1. Website is http://www.pogoda-sv.ru/?mode=airdata
2. Under the hood, this map uses an API, so scraper just calls it and stores the returned JSON in `data/volga/raw`.
3. “Volga region” here is just the area of activity of Volga branch of Russian Hydrometeorological Service, so it includes 5 subjects of the federation: Penza, Samara, Saratov, Uliyanovsk and Orenburg (with some cities in the corresponding regions).
4. Data is retrieved every day.

### FEERC (Clean Air)

1. “Clean Air” is a federal project for monitoring air pollution in most polluted cities of Russia.
2. The website is www.feerc.ru/uisem/portal/ and for each city there is a map (e. g. http://www.feerc.ru/uisem/portal/ad/norilsk). For some cities the map does not work, but if fact the map is common for all the cities (decrease the scale to see). Also, it includes the data for some cities which are not the part of the project. Under the hood, this map uses an API, so, like for Volga region, the scraper just calls this API and stores returned JSON in `data/feerc/raw`.
3. Data is retrieved evedy day.
4. The most interesting part of the data is `primsSS` element of every station. It contains the history of daily averages for a station. The items are not named, but their order coincides with the order of pollutants in `si` element.
