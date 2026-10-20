from collections.abc import AsyncIterator
from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlsplit

from src.infrastructure.provider.client import (
    EventsProviderClient,
    EventsProviderInvalidResponse,
)


def extract_cursor(next_url: str, changed_at: date) -> str:
    """Извлечь cursor из URL следующей страницы."""
    try:
        parsed_url = urlsplit(next_url)
    except ValueError as exc:
        raise EventsProviderInvalidResponse(
            "Events Provider returned an invalid next URL"
        ) from exc

    if parsed_url.path.rstrip("/") != "/api/events":
        raise EventsProviderInvalidResponse(
            "Events Provider returned an unexpected pagination endpoint"
        )

    query = parse_qs(parsed_url.query)
    cursors = query.get("cursor")

    if not cursors or len(cursors) != 1 or not cursors[0]:
        raise EventsProviderInvalidResponse(
            "Events Provider returned a next URL without a valid cursor"
        )

    next_changed_at = query.get("changed_at")

    if next_changed_at is not None and next_changed_at != [
        changed_at.isoformat()
    ]:
        raise EventsProviderInvalidResponse(
            "Pagination URL contains an unexpected changed_at value"
        )

    return cursors[0]


class EventsPaginator:
    """Асинхронный итератор по всем страницам мероприятий."""

    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: date,
    ) -> None:
        self._client = client
        self._changed_at = changed_at
        self._cursor: str | None = None

        self._events: list[dict[str, Any]] = []
        self._index = 0
        self._finished = False
        self._seen_cursors: set[str] = set()

    def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        return self

    async def __anext__(self) -> dict[str, Any]:
        while self._index >= len(self._events):
            if self._finished:
                raise StopAsyncIteration

            payload = await self._client.events(
                changed_at=self._changed_at,
                cursor=self._cursor,
            )

            events = payload.get("results")

            if not isinstance(events, list) or not all(
                isinstance(event, dict) for event in events
            ):
                raise EventsProviderInvalidResponse(
                    "Events response must contain a list of objects"
                )

            next_url = payload.get("next")

            if next_url is None:
                self._finished = True
            else:
                if not isinstance(next_url, str):
                    raise EventsProviderInvalidResponse(
                        "Events response contains an invalid next URL"
                    )

                next_cursor = extract_cursor(
                    next_url,
                    self._changed_at,
                )

                if next_cursor in self._seen_cursors:
                    raise EventsProviderInvalidResponse(
                        "Events Provider returned a repeated cursor"
                    )

                self._seen_cursors.add(next_cursor)
                self._cursor = next_cursor

            self._events = events
            self._index = 0

        event = self._events[self._index]
        self._index += 1

        return event
