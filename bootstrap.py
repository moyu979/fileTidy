import argparse
from application.app import App
from infra.config.config import Config
from infra.persistence.database import build_session_factory

def bootstrap(args: argparse.Namespace):
    config = Config(args)

    session_factory, engine = build_session_factory(config["database"]["url"])
    print(config)
    return App()
