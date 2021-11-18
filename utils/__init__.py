import datetime
import pathlib

import bs4
import requests


def to_csv_data(cells, n_cols):
    n_rows = len(cells) // n_cols
    return [','.join(cells[k * n_cols:(k+1) * n_cols]) for k in range(n_rows)]


def scrape(endpoint, html):
    # So far, only the page displaying the top 10 countries by censorship events needs to be scraped
    lines = []
    if 'top_10' in endpoint:
        cells = [word for word in html.find('table').stripped_strings]
        lines = to_csv_data(cells, 3)

    return lines


class Endpoint:
    def __init__(self, api, **kwargs):
        self.__path = pathlib.Path(kwargs.get('path'))
        self.__needs_scraping = 'htm' in self.__path.suffix
        self.__session = api.session
        self.__url = f'{api.url}/{str(self.__path)}'

    @property
    def needs_scrapping(self):
        return self.__needs_scraping

    def get(self, params):
        return self.__session.get(self.__url, params=params)


class API:
    def __init__(self, **kwargs):
        self.__session = requests.Session()
        self.__session.headers.update({'User-Agent': ''.join([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
        ])})
        self.__base_url = kwargs.get('base_url')
        self.__params = {
            'start': kwargs.get('start').isoformat(),
            'end': kwargs.get('end').isoformat(),
        }
        self.__endpoints = {name: Endpoint(self, **{'path': path}) for name, path in kwargs.get('endpoints').items()}

    @property
    def url(self):
        return self.__base_url

    @property
    def session(self):
        return self.__session

    @property
    def endpoints(self):
        return self.__endpoints

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.__session.close()

    def save(self, name, path):
        endpoint = self.__endpoints.get(name)
        data = endpoint.get(self.__params).text
        if endpoint.needs_scrapping:
            # If the endpoint returns HTML data, the values need to be extracted into some lines
            # which could be saved to a CSV file.
            html = bs4.BeautifulSoup(data, 'lxml')
            lines = scrape(name, html)
        else:
            # The first 5 lines in CSV files downloaded from Tor Metrics need to be removed,
            # as they break the format and reflect the sent request as a comment.
            lines = data.split('\n')[5:]
        with open(path, 'w', encoding='utf-8') as output_file:
            output_file.writelines('\n'.join(lines))


def bulk_download():
    base_dir = pathlib.Path(__file__).resolve().parent
    data_dir = base_dir / 'data'

    if not data_dir.exists():
        data_dir.mkdir()

    kwargs = {
        'base_url': 'https://metrics.torproject.org',
        'start': datetime.date(2020, 3, 1),
        'end': datetime.date(2021, 2, 28),
        'endpoints': {
            'relay_users': 'userstats-relay-country.csv',
            'bridge_users_by_country': 'userstats-bridge-country.csv',
            'top_10_countries_by_censorship_events': 'userstats-censorship-events.html',
            'relays_and_bridges': 'networksize.csv',
            'relays_by_tor_versions': 'versions.csv',
            'relays_by_platform': 'platforms.csv',
            'total_bandwidth': 'bandwidth.csv',
            'ad_cs_bandwidth': 'bandwidth-flags.csv',
            'bandwidth_by_ip_version': 'advbw-ipv6.csv',
            'tor_downloads': 'torperf.csv',
            'tor_download_timeouts_and_failures': 'torperf-failures.csv',
            'circuit_build_times': 'onionperf-buildtimes.csv',
            'circuit_latency': 'onionperf-latencies.csv',
            'throughput': 'onionperf-throughput.csv',
            'all_versions_traffic': 'hidserv-rend-relayed-cells.csv',
            'v2_traffic': 'hidserv-dir-onions-seen.csv',
            'v3_traffic': 'hidserv-dir-v3-onions-seen.csv',
            'tor_browser_updates_and_downloads': 'webstats-tb.csv',
            'tor_browser_upd_and_dl_by_platform': 'webstats-tb-platform.csv'
        }
    }

    with API(**kwargs) as api:
        for endpoint in api.endpoints.keys():
            api.save(endpoint, data_dir / f'{endpoint}.csv')
