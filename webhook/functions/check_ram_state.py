import datetime
import os
import time

import requests

# from rocketry import Rocketry
from dotenv import load_dotenv
from httpx import Client

# from rocketry.conds import every, time_of_day
from requests.exceptions import ChunkedEncodingError

load_dotenv()
# app = Rocketry()


def load_env(var):
    return os.environ.get(var, os.getenv(var))


APP = "WEBHOOK"
TIMEOUT = 120
IS_LOCALHOST = load_env("IS_LOCALHOST")
CYCLE_API = (
    load_env("CYCLE_API_LOCAL_URL") if IS_LOCALHOST else load_env("CYCLE_API_URL")
)
HEROKU_API_KEY = load_env("HEROKU_API_KEY")
HEROKU_API = load_env("HEROKU_API_URL")
HEROKU_APP_NAME = "woz"
DYNO_NAME = ["worker.1", "web.1"]
ALLOWED_DYNO_STATES = ["starting", "up"]
NOT_ALLOWED_DYNO_STATES = ["crashed", "down", "idle"]
# CHECK_STATE_INTERVAL = every("2 minutes") & time_of_day.between("08:00", "21:00")
WEBHOOK_SEND_REPORT_URL = f"{CYCLE_API}/control/report/send-message"
LOG_STREAM_URL_RETRIEVE = f"/apps/{HEROKU_APP_NAME}/log-sessions"

client_request_header = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
    "Content-Type": "application/json",
}


def currently_datetime():
    return datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")


def send_report(client: Client, text: str, **kwargs):
    request = client.request(
        "POST",
        WEBHOOK_SEND_REPORT_URL,
        params={"group": "REPORT"},
        json={"text": text},
        headers={"Accept": "application/json"},
    )
    return request.text


def restart_dynos(client: Client, text=None):
    client.delete(f"/apps/{HEROKU_APP_NAME}/dynos", headers=client_request_header)
    time.sleep(2)
    report = send_report(
        client,
        f"{APP}: Todos os dynos foram reiniciado para resolver problemas Checked-In: {currently_datetime()}"
        if not text
        else text,
    )
    print(report)
    return


def refresh_log_stream(client: Client):
    def handle_env_file(stream_url: str):
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as file:
            for line in lines:
                if line.startswith("LOG_STREAM_URL"):
                    file.write(f"LOG_STREAM_URL='{stream_url}'\n")
                else:
                    file.write(line)

    response = client.post(LOG_STREAM_URL_RETRIEVE)
    new_stream_log_url = response.json()["logplex_url"].replace(
        "tail=false", "tail=true"
    )
    print(f"\nNew Stream log url: {new_stream_log_url}")
    handle_env_file(new_stream_log_url)
    print(f"\nENV File modificado: (LOG_STREAM_URL='{new_stream_log_url}')")
    return new_stream_log_url


# @app.task(CHECK_STATE_INTERVAL)
def check_memory():
    print(CYCLE_API)
    client = Client(base_url=HEROKU_API, headers=client_request_header, timeout=TIMEOUT)
    log_stream_url = load_env("LOG_STREAM_URL")
    while True:
        try:
            response = requests.get(log_stream_url, stream=True)

            if response.status_code not in range(200, 202):
                print("Esse link de stream expirou, buscando um novo")
                log_stream_url = refresh_log_stream(client)
                continue
            else:
                print("\n\nOuvindo logs do sistema web:")
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        # print(decoded_line)
                        if (
                            "heroku[web.1]: Error R14 (Memory quota exceeded)"
                            in decoded_line
                            or "heroku[worker.1]: Error R14 (Memory quota exceeded)"
                            in decoded_line
                        ):
                            print(
                                "Memory quota exceeded error found. Restarting dynos..."
                            )
                            restart_dynos(
                                client,
                                text=f"Todos os dynos foram reiniciado para resolver problemas com memória RAM Checked-In: {currently_datetime()}",
                            )
                            time.sleep(1)
                            continue
        except ChunkedEncodingError as e:
            print(f"Erro de Chunked Encoding: {e}", "Retrieving new stream log url")
            continue

        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}", "Retrieving new stream log url")
            continue


if __name__ == "__main__":
    check_memory()
