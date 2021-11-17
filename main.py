import datetime
import pathlib
import requests


class Endpoint:
    def __init__(self, api, **kwargs):
        self.__method = kwargs.get('method')
        self.__path = pathlib.Path(kwargs.get('path'))
        self.__needs_scrapping = 'htm' in self.__path.suffix
        self.__session = api.session
        self.__url = f'{api.url}/{str(self.__path)}'

    def get(self, params=None, **kwargs):
        return self.__session.get(self.__url, params=params, **kwargs)


class API:
    def __init__(self, **kwargs):
        self.__session = requests.Session()
        self.__session.headers.update({'User-Agent': ''.join([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '(KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'
        ])})
        self.__base_url = kwargs.get('base_url')
        self.__default_params = {
            'start': kwargs.get('start').isoformat(),
            'end': kwargs.get('end').isoformat(),
        }
        self.__endpoints = {name: Endpoint(self, **properties) for name, properties in kwargs.get('endpoints').items()}

    @property
    def url(self):
        return self.__base_url

    @property
    def session(self):
        return self.__session

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.__session.close()

    def save(self, name, path, params):
        params |= self.__default_params
        with open(path, 'w', encoding='utf-8') as output_file:
            response = self.__endpoints.get(name).get(params=params)
            output_file.writelines(response.text)


def main():
    base_dir = pathlib.Path(__file__).resolve().parent
    data_dir = base_dir / 'data'

    if not data_dir.exists():
        data_dir.mkdir()

    kwargs = {
        'base_url': 'https://metrics.torproject.org',
        'start': datetime.date(2020, 3, 1),
        'end': datetime.date(2021, 2, 28),
        'endpoints': {
            'relay_users': {
                'method': 'GET',
                'path': 'userstats-relay-country.csv'
            }
        }
    }

    with API(**kwargs) as api:
        api.save('relay_users', data_dir / 'relay_users.csv', params={
            'start': '2021-08-10',
            'end': '2021-11-16',
            'country': 'all',
            'events': 'off'
        })


if __name__ == '__main__':
    main()
