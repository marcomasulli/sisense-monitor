from .database import session, FailedBuilds
from .config import Config
from urllib.parse import urljoin
from datetime import datetime, timedelta
import requests
import pandas as pd
import traceback
from time import sleep


def record_failure(oid, datamodel_id, datamodel_title, instance_id):
    try:
        new_failed_build = FailedBuilds(
            oid=oid,
            datamodel_id=datamodel_id,
            datamodel_title=datamodel_title,
            instance_id=instance_id,
        )
        session.add(new_failed_build)
        session.commit()
        # insert oid and data in db
        print("Failed build recorded in db")
        return True
    except Exception:
        print(traceback.print_exc())


def save_log_to_sp(
    log,
    datamodel_title,
    ts,
    site_url=Config.SP_ROOT_URL,
    client_id=Config.SP_ID,
    client_secret=Config.SP_SECRET,
    target_folder_name="Shared Documents/Sisense Monitor/BuildLogs",
):

    from office365.runtime.auth.user_credential import UserCredential
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.authentication_context import AuthenticationContext
    import json

    # connect to SP
    context_auth = AuthenticationContext(url=site_url)
    context_auth.acquire_token_for_app(client_id=client_id, client_secret=client_secret)

    ctx = ClientContext(site_url, context_auth)
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()

    target_folder = web.get_folder_by_server_relative_url(target_folder_name)
    filename = f"{datamodel_title} {ts} buildlog.json"
    try:
        target_file = target_folder.upload_file(
            filename, bytes(json.dumps(log, indent=4), encoding="utf-8")
        )
        ctx.execute_query()
        print("OK - Log saved to SP")
        return target_file.serverRelativeUrl
    except Exception as e:
        print(traceback.print_exc())
        return


def get_logs(datamodel_id, datamodel_title):
    # get log
    log = requests.get(
        f"{Config.SISENSE_URL}/v1/elasticubes/{datamodel_id}/buildLogs",
        headers=Config.SISENSE_HEADERS,
    )
    # convert to json
    json_log = log.json()
    # get ts and error message
    for l in json_log:
        if "verbosity" in l.keys():
            if l.get("verbosity") == "Error":
                ts = l.get("timestamp") or "1900-01-01T00:00:00.00000"
                print(ts)
                error_message = l.get("message") or "No error message"
                print(error_message)

    # transform ts to string
    ts_dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    ts_filestring = ts_dt.strftime("%Y-%m-%dT%H%M")

    save_link = save_log_to_sp(json_log, datamodel_title, ts_filestring)
    ts_cardstring = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
    error_dict = {
        "timestamp": ts_cardstring,
        "error_message": error_message,
        "file_link": save_link,
    }

    print(error_dict)

    return error_dict


def make_teams_card(datamodel_name, ts, error_message, save_link):

    card_json = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": f"New Failed Cube: {datamodel_name}",
        "sections": [
            {
                "activityTitle": f"New Failed Build: {datamodel_name}",
                "facts": [
                    {"name": "TimeStamp", "value": f"{ts}"},
                    {"name": "Error Log", "value": f"{error_message}"},
                    {"name": "Full Log Link", "value": f"{save_link}"},
                ],
                "markdown": False,
            }
        ],
    }

    return card_json


def send_teams_card(card_json):
    response = requests.post(
        Config.TEAMS_CONNECTOR_URL,
        headers={"Content-Type": "application/json"},
        json=card_json,
    )
    return response


def check_builds():
    """Base task"""
    response = requests.get(
        url=urljoin(Config.SISENSE_URL, "v2/builds"), headers=Config.SISENSE_HEADERS
    )
    builds = pd.DataFrame(data=response.json())
    failed_builds = builds.loc[(builds.status == "failed")]
    # for each failed cube:
    for build in failed_builds.to_dict(orient="records"):
        # check if failed cube is already recorded (oid), if not record
        recorded_failure = (
            session.query(FailedBuilds).filter(FailedBuilds.oid == build["oid"]).first()
        )
        if recorded_failure is None:
            # record
            record_failure(
                build["oid"],
                build["datamodelId"],
                build["datamodelTitle"],
                build["instanceId"],
            )
            # save log and get elements for log card
            error_dict = get_logs(build["datamodelId"], build["datamodelTitle"])
            # prepare card (so look into log)
            card = make_teams_card(
                build["datamodelTitle"],
                error_dict["timestamp"],
                error_dict["error_message"],
                error_dict["file_link"],
            )
            # send card
            send_teams_card(card)
            return error_dict
