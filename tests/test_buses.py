from __future__ import annotations

from dataclasses import dataclass

from mentat.core import Command, Query, CommandBus, QueryBus, Result


@dataclass(slots=True)
class Ping(Command):
    pass


@dataclass(slots=True)
class GetNumber(Query[int]):
    pass


def test_command_bus_dispatch():
    bus = CommandBus()

    def handle(_cmd: Ping) -> Result[int]:
        return Result.success(42)

    bus.register(Ping, handle)
    res = bus.dispatch(Ping())
    assert res.ok and res.value == 42


def test_query_bus_ask():
    bus = QueryBus()

    def handle(_q: GetNumber) -> Result[int]:
        return Result.success(7)

    bus.register(GetNumber, handle)
    res = bus.ask(GetNumber())
    assert res.ok and res.value == 7
