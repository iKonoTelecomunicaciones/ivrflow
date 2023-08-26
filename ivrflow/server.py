from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.log import agi_server_logger as Logger
from aioagi.urldispathcer import AGIView

from repository import Flow as FlowModel
from flow import Flow
from logging import getLogger, Logger
import logging.config

log: Logger = getLogger()


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "(%(levelname)s) | %(name)s | [%(asctime)s]: "
            'File %(pathname)s:%(lineno)s" - %(funcName)s() | %(message)s'
        },
        "additional_verbose": {
            "format": "\n\033[1;34m(%(levelname)s) | %(name)s | [%(asctime)s]:\n"
            'File \033[3;38;5;226m"%(pathname)s:%(lineno)s"\033[23;38;5;87m - %(funcName)s()\n'
            '\033[1;34mMessage \033[3;38;5;198m"%(message)s"\n\033[23;0;0m',
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "additional_verbose",
        },
    },
    "loggers": {
        "aioagi": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "py.warnings": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "asyncio": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}


class IVRFlow(AGIView):
    current_node = "start"

    async def sip(self):
        log.critical("Estamos en el sip")
        await self.algorithm()

    async def local(self):
        await self.algorithm()

    async def dahdi(self):
        await self.algorithm()

    async def algorithm(self):
        flow_model = FlowModel.load_flow(self.flow_path)
        flow = Flow(flow_model)
        log.critical(flow.nodes)

        node = flow.node(self.current_node)
        node.run()

    @property
    def flow_path(self):
        return self.request.path.strip("/")


if __name__ == "__main__":
    logging.config.dictConfig(LOGGING)
    app = AGIApplication()
    app.router.add_route("*", "/{key:.+}", IVRFlow)
    runner.run_app(app)
