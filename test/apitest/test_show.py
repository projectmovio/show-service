import time

import requests

from apitest.conftest import API_URL, BASE_HEADERS


def test_post_show():
    res = requests.post(f"{API_URL}/show?tvmaze_id=20", headers=BASE_HEADERS)
    assert res.status_code == 200
    time.sleep(1)
