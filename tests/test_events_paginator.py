from datetime import date
from unittest.mock import AsyncMock, call

import pytest

from src.infrastructure.provider.client import (
    EventsProviderInvalidResponse,
)
from src.infrastructure.provider.paginator import (
    EventsPaginator,
)


@pytest.mark.asyncio
async def test_paginator_iterates_over_all_pages() -> None:
    changed_at = date(2000, 1, 1)
    client = AsyncMock()

    client.events.side_effect = [
        {
            "next": (
                "http://provider.test/api/events/"
                "?changed_at=2000-01-01&cursor=abc"
            ),
            "results": [{"id": "1"}, {"id": "2"}],
        },
        {
            "next": None,
            "results": [{"id": "3"}],
        },
    ]

    paginator = EventsPaginator(client, changed_at)

    result = [event["id"] async for event in paginator]

    assert result == ["1", "2", "3"]

    assert client.events.await_args_list == [
        call(changed_at=changed_at, cursor=None),
        call(changed_at=changed_at, cursor="abc"),
    ]


@pytest.mark.asyncio
async def test_paginator_handles_empty_page() -> None:
    client = AsyncMock()

    client.events.side_effect = [
        {
            "next": (
                "http://provider.test/api/events/"
                "?changed_at=2000-01-01&cursor=abc"
            ),
            "results": [],
        },
        {
            "next": None,
            "results": [{"id": "1"}],
        },
    ]

    paginator = EventsPaginator(client, date(2000, 1, 1))

    result = [event["id"] async for event in paginator]

    assert result == ["1"]
    assert client.events.await_count == 2


@pytest.mark.asyncio
async def test_paginator_rejects_unexpected_next_url() -> None:
    client = AsyncMock()

    client.events.return_value = {
        "next": "http://provider.test/api/other/?cursor=abc",
        "results": [],
    }

    paginator = EventsPaginator(client, date(2000, 1, 1))

    with pytest.raises(EventsProviderInvalidResponse):
        await anext(paginator)


@pytest.mark.asyncio
async def test_paginator_rejects_repeated_cursor() -> None:
    client = AsyncMock()

    page = {
        "next": (
            "http://provider.test/api/events/?changed_at=2000-01-01&cursor=abc"
        ),
        "results": [],
    }

    client.events.side_effect = [page, page]

    paginator = EventsPaginator(client, date(2000, 1, 1))

    with pytest.raises(EventsProviderInvalidResponse):
        async for _ in paginator:
            pass
