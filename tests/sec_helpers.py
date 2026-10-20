"""Injected clocks and transports for synthetic SEC tests; never access the network."""

from collections.abc import Mapping
from datetime import UTC, datetime

from sec_research.adapters.sec.client import LocalLimiter, Response, SecClient, SecPolicy


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeTransport:
    def __init__(self, *responses: Response | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, Mapping[str, str], float, int]] = []

    def __call__(
        self, url: str, headers: Mapping[str, str], timeout: float, max_bytes: int
    ) -> Response:
        self.requests.append((url, headers, timeout, max_bytes))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def client(transport: FakeTransport, clock: Clock, **policy: object) -> SecClient:
    config = SecPolicy.model_validate(
        {"user_agent": "SyntheticTests contact@example.test", **policy}
    )
    return SecClient(
        config,
        transport=transport,
        limiter=LocalLimiter(clock=clock.now, sleep=clock.sleep),
        clock=clock.now,
        sleep=clock.sleep,
        jitter=lambda: 0,
        now=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )
