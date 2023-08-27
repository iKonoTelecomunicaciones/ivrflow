from logging import Logger, getLogger

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.log import agi_server_logger as Logger
from aioagi.urldispathcer import AGIView

from .config import config
from .flow import Flow
from .nodes import Base
from .repository import Flow as FlowModel

log: Logger = getLogger("ivrflow.main")


class IVRFlow(AGIView):
    current_node = "start"

    async def sip(self):
        await self.algorithm()

    async def local(self):
        await self.algorithm()

    async def dahdi(self):
        await self.algorithm()

    async def algorithm(self):
        Base.init_cls(config=config, asterisk_conn=self.request)
        flow_model = FlowModel.load_flow(self.flow_path)
        flow = Flow(flow_data=flow_model)
        node = flow.node(self.current_node)
        await node.run()

    @property
    def flow_path(self):
        return self.request.path.strip("/")


if __name__ == "__main__":
    app = AGIApplication()
    app.router.add_route("*", "/{key:.+}", IVRFlow)
    runner.run_app(app)
