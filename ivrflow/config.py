import logging.config

from mautrix.util.config import BaseFileConfig, ConfigUpdateHelper


class Config(BaseFileConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        copy_dict = helper.copy_dict
        # Logging
        copy_dict("logging")


def init_config():
    config = Config(path="/data/config.yaml", base_path="ivrflow/sample-config.yaml")
    config.load_and_update()
    logging.config.dictConfig(config["logging"])
    return config


config = init_config()
