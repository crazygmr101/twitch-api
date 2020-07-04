from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional, TYPE_CHECKING
import traceback

import websockets

from twitch import Command, CommandRegisteredError, Context, Event, Message, User

if TYPE_CHECKING:
    import twitch


class Bot:
    def __init__(self, oauth: str, channel: str, nick: str):
        self._oauth = oauth
        self._channel = channel
        self.name: str = ""
        self._nick: str = nick
        self._on_message: List[Callable[[Any], Awaitable[Any]]] = []
        self._commands: Dict[str, Command] = {}
        self._on_ready: List[Callable[[], Awaitable[Any]]] = []
        self._ws: Optional[websockets.WebSocketCommonProtocol] = None
        self._users: List[twitch.core.User] = []
        self._room_id: str = ""
        self.loop = asyncio.get_event_loop()

    def run(self):
        logging.info("BOT: Starting coroutine")
        self.loop.run_until_complete(self._run())

    async def _run(self):
        logging.info("BOT: Connecting to websocket")
        self._ws = await websockets.connect("wss://irc-ws.chat.twitch.tv:443")
        logging.info("BOT: Connected to websocket, authenticating")
        await self._ws.send(f"PASS {self._oauth}")
        logging.info("PASS {{REDACTED}}")
        await self._send(f"NICK {self._nick}")
        logging.info(await self._ws.recv())
        logging.info("BOT: Requesting tag and command capabilities")
        await self._send("CAP REQ :twitch.tv/tags twitch.tv/commands")
        await self._recv()
        logging.info("BOT: Authenticated, joining channel")
        await self._send(f"JOIN {self._channel}")
        ack = await self._recv()
        self.name = ack.split(":")[1].split("!")[0]
        coros = [coro_func() for coro_func in self._on_ready]
        await asyncio.gather(*coros)
        while not self._ws.closed:
            msg: str = (await self._recv()).strip()
            if msg == "PING :tmi.twitch.tv":
                logging.info("Got PING, sending PONG")
                await self._send("PONG :tmi.twitch.tv")
                continue
            if "PRIVMSG" in msg:
                message: twitch.Message = Message(msg, self)
                coros = [coro_func(message) for coro_func in self._on_message]
                await asyncio.gather(*coros)
                if message.content.startswith("!") and not message.is_bot:
                    name = message.content.lstrip("!").split(" ")[0]
                    if name in self._commands:
                        # noinspection PyBroadException
                        try:
                            await self._commands[name].__call__(Context(message, self._commands[name]))
                        except Exception as e:
                            print(f"Ignoring exception in command {name}")
                            traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
                continue

    def add_on_ready(self, coro_func: Callable[[], Awaitable[Any]]):
        self._on_ready.append(coro_func)

    async def _send(self, message: str):
        logging.info(f"SEND << {message}")
        await self._ws.send(message)

    async def _recv(self) -> str:
        m = await self._ws.recv()
        if m.split(" ")[1] == "421":
            logging.warning(f"RECV >> {m}")
        else:
            logging.info(f"RECV >> {m}")
        return m

    async def send(self, message: str):
        await self._send(f"PRIVMSG {self._channel} :{message}")

    def event(self, name: str = None):
        def wrapper(coro_func: Callable[[Any], Awaitable[Any]]):
            event = Event(typ=name or coro_func.__name__, coro_func=coro_func)
            if event.typ == "on_ready":
                logging.info(f"Appended on_ready {coro_func.__name__}")
                self._on_ready.append(event)
            if event.typ == "on_message":
                logging.info(f"Appended on_message {coro_func.__name__}")
                self._on_message.append(event)
            return event

        return wrapper

    def command(self, name: str = None):
        def wrapper(coro_func: Callable[[Any], Awaitable[Any]]):
            cmd = Command(name=name or coro_func.__name__, coro_func=coro_func)
            if cmd.name in self._commands:
                logging.info(f"Command {cmd.name} {coro_func.__name__} already registered")
                raise CommandRegisteredError(cmd.name)
            self._commands[cmd.name] = cmd
            logging.info(f"Command {cmd.name} {coro_func.__name__} registered")
            return cmd

        return wrapper

    def _get_user(self, name: str) -> twitch.core.User:
        pass

    async def _send_priv(self, message: str):
        await self._send(f":tmi.twitch.tv PRIVMSG {self._channel} :{message}")

    def get_command(self, name: str):
        return self._commands.get(name, None)

    async def timeout_user(self, user: User, duration: int = 600):
        await self._send_priv(f"/timeout {user.display_name} {duration}")

    async def untimeout_user(self, user: User):
        await self._send_priv(f"/untimeout {user.display_name}")

    async def clear_chat(self):
        await self._send_priv("/clear")
