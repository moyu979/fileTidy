from apps.core.initer import init
from apps.infra.restapi.restapi import start_rest_api

if __name__ == "__main__":
    init()
    start_rest_api()