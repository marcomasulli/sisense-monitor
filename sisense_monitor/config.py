import os
import requests


class Config(object):
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite"
    # sisense
    SISENSE_URL = os.environ.get("SISENSE_URL") or "https://domain.sisense.com/api"
    SISENSE_UN = os.environ.get("SISENSE_UN") or "Username"
    SISENSE_PW = os.environ.get("SISENSE_PW") or "Password"
    SISENSE_REQ = requests.post(
        url=f"{SISENSE_URL}/v1/authentication/login",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"username": SISENSE_UN, "password": SISENSE_PW},
    )
    SISENSE_KEY = "Bearer {}".format(SISENSE_REQ.json()["access_token"])
    SISENSE_HEADERS = {
        "authorization": SISENSE_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    # teams connector url
    TEAMS_CONNECTOR_URL = os.environ.get("TEAMS_CONNECTOR_URL") or "https://teams.connector.url"
    # sp credentials
    SP_ROOT_URL = (
        "https://teams.sharepoint.com/sites/team"
    )
    SP_ID = os.environ.get("SP_ID") or "SharepointId"
    SP_SECRET = os.environ.get("SP_SECRET") or "SharepointSecret"
