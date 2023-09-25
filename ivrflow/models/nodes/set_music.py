from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class SetMusic(FlowObject):
    """
    ## Musid on hold a channel.

    Enable/Disable Music on hold generator.

    content:

    ```
    - id: p1
      type: set_music
      music_class: default
      toggle: "on"
      o_connection: m2
    ```
    """

    music_class: str = ib(default="default")
    toggle: str = ib(default="on")
    o_connection: str = ib(default=None)
