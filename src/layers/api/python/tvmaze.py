import requests

import logger

log = logger.get_logger(__name__)


class Error(Exception):
    pass


class HTTPError(Error):
    pass


class TvMazeApi:
    def __init__(self):
        self.base_url = "https://api.tvmaze.com"

        log.debug("TvMazeApi base_url: {}".format(self.base_url))

    def get_day_updates(self):
        res = requests.get(f"{self.base_url}/updates/shows?since=day")
        if res.status_code != 200:
            raise HTTPError(f"Unexpected status code: {res.status_code}")
        return res.json()
