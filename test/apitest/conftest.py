import os

API_URL = os.getenv("API_URL")
BASE_HEADERS = {
    "Authorization": os.getenv("TOKEN")
}
