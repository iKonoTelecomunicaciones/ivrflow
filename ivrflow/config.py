import logging.config
import random
import string

from mautrix.util.config import BaseFileConfig, ConfigUpdateHelper


class Config(BaseFileConfig):
    @staticmethod
    def _new_token() -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=64))

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        base = helper.base
        copy = helper.copy
        copy_dict = helper.copy_dict
        # Ivrflow
        copy("ivrflow.database")
        copy_dict("ivrflow.database_opts")
        copy_dict("ivrflow.timeouts")
        copy("ivrflow.load_flow_from")
        copy("ivrflow.enable_asyncio_debug")
        copy("ivrflow.backup_limit")

        # Logging
        copy_dict("logging")

        # API Server
        copy("server.hostname")
        copy("server.port")
        copy("server.public_url")
        copy("server.base_path")
        copy("server.unshared_secret")

        shared_secret = self["server.unshared_secret"]
        if shared_secret is None or shared_secret == "generate":
            base["server.unshared_secret"] = self._new_token()
        else:
            base["server.unshared_secret"] = shared_secret


def init_config():
    config = Config(path="/data/config.yaml", base_path="ivrflow/sample-config.yaml")
    config.load_and_update()
    logging.config.dictConfig(config["logging"])
    return config


config = init_config()
