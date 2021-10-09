import requests

import logger

log = logger.get_logger(__name__)


class Error(Exception):
    pass


class HTTPError(Error):

    def __init__(self, code):
        Error.__init__(self, f"Unexpected status code: {code}")
        self.code = code
    

class TvMazeApi:
    def __init__(self):
        self.base_url = "https://api.tvmaze.com"

        log.debug("TvMazeApi base_url: {}".format(self.base_url))

    def get_show(self, show_id):
        res = requests.get(f"{self.base_url}/shows/{show_id}")

        if res.status_code != 200:
            raise HTTPError(res.status_code)
        return res.json()

    def get_episode(self, episode_id):
        res = requests.get(f"{self.base_url}/episodes/{episode_id}")

        if res.status_code != 200:
            raise HTTPError(res.status_code)
        return res.json()

    def get_day_updates(self):
        res = requests.get(f"{self.base_url}/updates/shows?since=day")
        if res.status_code != 200:
            raise HTTPError(res.status_code)
        return res.json()

    def get_show_episodes(self, show_id):
        res = requests.get(
            f"{self.base_url}/shows/{show_id}/episodes?specials=1"
        )

        if res.status_code != 200:
            raise HTTPError(res.status_code)
        return res.json()

    def get_show_episodes_count(self, show_id):
        episodes = self.get_show_episodes(show_id)

        ep_count = 0
        special_count = 0

        for e in episodes:
            if e["type"] == "regular":
                ep_count += 1
            else:
                special_count += 1

        return {
            "ep_count": ep_count,
            "special_count": special_count,
        }
