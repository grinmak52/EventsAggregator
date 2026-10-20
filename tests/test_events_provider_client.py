from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest

from src.infrastructure.provider.client import (
    EventsProviderClient,
    EventsProviderConfigurationError,
    EventsProviderHTTPError,
)


def make_response(
    payload: dict,
    status_code: int = 200,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "http://provider.test/api/events/",
    )
    return httpx.Response(
        status_code=status_code,
        json=payload,
        request=request,
    )


def make_client() -> tuple[EventsProviderClient, AsyncMock]:
    http_client = AsyncMock(spec=httpx.AsyncClient)

    client = EventsProviderClient(
        base_url="http://provider.test",
        api_key="test-api-key",
        http_client=http_client,
    )

    return client, http_client


@pytest.mark.asyncio
async def test_events_sends_api_key_and_changed_at() -> None:
    client, http_client = make_client()

    http_client.request.return_value = make_response(
        {
            "next": None,
            "previous": None,
            "results": [],
        }
    )

    result = await client.events(date(2000, 1, 1))

    assert result["results"] == []

    http_client.request.assert_awaited_once_with(
        "GET",
        "api/events/",
        headers={"x-api-key": "test-api-key"},
        params={"changed_at": "2000-01-01"},
    )


@pytest.mark.asyncio
async def test_seats_returns_available_seats() -> None:
    client, http_client = make_client()

    http_client.request.return_value = make_response(
        {"seats": ["A1", "A3", "B1"]}
    )

    seats = await client.seats("event-123")

    assert seats == ["A1", "A3", "B1"]

    http_client.request.assert_awaited_once_with(
        "GET",
        "api/events/event-123/seats/",
        headers={"x-api-key": "test-api-key"},
    )


@pytest.mark.asyncio
async def test_register_returns_ticket_id() -> None:
    client, http_client = make_client()

    http_client.request.return_value = make_response(
        {"ticket_id": "ticket-123"},
        status_code=201,
    )

    ticket_id = await client.register(
        event_id="event-123",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )

    assert ticket_id == "ticket-123"

    http_client.request.assert_awaited_once_with(
        "POST",
        "api/events/event-123/register/",
        headers={"x-api-key": "test-api-key"},
        json={
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15",
        },
    )


@pytest.mark.asyncio
async def test_provider_http_error_is_translated() -> None:
    client, http_client = make_client()

    http_client.request.return_value = make_response(
        {"detail": "Unauthorized"},
        status_code=401,
    )

    with pytest.raises(EventsProviderHTTPError) as error:
        await client.events(date(2000, 1, 1))

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_api_key_prevents_request() -> None:
    http_client = AsyncMock(spec=httpx.AsyncClient)

    client = EventsProviderClient(
        base_url="http://provider.test",
        api_key="",
        http_client=http_client,
    )

    with pytest.raises(EventsProviderConfigurationError):
        await client.events(date(2000, 1, 1))

    http_client.request.assert_not_awaited()
