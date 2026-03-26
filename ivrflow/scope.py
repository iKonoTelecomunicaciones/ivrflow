from dataclasses import dataclass

from .db.channel import Channel
from .types import Scopes


@dataclass
class ScopeHandler:
    model: Channel
    scope: Scopes

    def get_scope_vars(self) -> dict:
        vars = self.model._variables

        if self.scope.value not in vars:
            vars[self.scope.value] = {}

        return vars[self.scope.value]

    async def update(self) -> None:
        await self.model.update_variables()


class Scope:
    def __init__(self, channel: Channel):
        self.channel = channel

    def resolve(self, scope: Scopes) -> ScopeHandler:
        if scope in (Scopes.ROUTE, Scopes.HOOK):
            return ScopeHandler(model=self.channel, scope=scope)

        raise ValueError(f"Unknown scope: {scope}")
