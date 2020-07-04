from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import twitch


class Converter:
    async def convert(self, bot: twitch.Bot, arg):
        raise NotImplementedError("This must be implemented in derived classes")
