from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    import twitch


class User:
    def __init__(self, msg_tags: str):
        tags = {}
        for i in msg_tags.strip("@ ").split(";"):
            _key, _value = i.split("=")
            tags[_key] = _value
        self.display_name: str = tags["display-name"]
        self.color: str = tags["color"]
        self.mod = (tags["mod"] == "1")
        self.id: str = tags["user-id"]
        badges = {}
        for i in tags["badges"].split(","):
            _key, _value = i.split("/")
            badges[_key] = _value
        if tags["badge-info"] == "":
            self.sub_length = 0
        else:
            self.sub_length = int(tags["badge-info"])
        self.broadcaster = (badges.get("broadcaster", 0) == '1')


# @badge-info=;
# badges=broadcaster/1;
# client-nonce=a70e66582ebe75b653e93827c4f156ab;
# color=;
# display-name=sturdy_bot;
# emotes=;
# flags=;
# id=f8209657-3ede-47bc-a314-45d7f4ee5dd3;
# mod=0;room-id=550988270;
# subscriber=0;
# tmi-sent-ts=1593966079775;
# turbo=0;user-id=550988270;
# user-type= :sturdy_bot!sturdy_bot@sturdy_bot.tmi.twitch.tv PRIVMSG #sturdy_bot :hi

class Message:
    """
    Represents a twitch Message
    """

    def __init__(self, message: str, bot: twitch.Bot):
        self.message = message
        self.bot = bot
        msg_tags, data, content = message.split(":")[0], message.split(":")[1], ":".join(message.split(":")[2:])
        self.content: str = content
        self.user = User(msg_tags)
        self.is_bot = self.user.display_name == bot.name
        tags = {}
        for i in msg_tags.strip("@ ").split(";"):
            _key, _value = i.split("=")
            tags[_key] = _value
        self.id: str = tags["id"]


class Context:
    def __init__(self, message: Message, command: Command):
        self.original = message
        self.bot = message.bot
        self.content = message.content
        _tok = message.content.lstrip("!").split(" ")
        self.command_name = _tok[0]
        if len(_tok) > 1:
            self.params = " ".join(_tok[1:])
        else:
            self.params = None

    def send(self, message: str):
        return self.bot.send(message)


class Event:
    def __init__(self, typ: str, coro_func: Callable[[Any], Awaitable[Any]]):
        self.typ = typ
        self.coro_func = coro_func

    def __call__(self, *args, **kwargs):
        return self.coro_func(*args, **kwargs)


class Command:
    def __init__(self, name: str, coro_func: Callable[[Any], Awaitable[Any]]):
        self.name = name
        self.coro_func = coro_func

    def __call__(self, *args, **kwargs):
        return self.coro_func(*args, **kwargs)
