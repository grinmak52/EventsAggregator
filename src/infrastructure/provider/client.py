from datetime import date
from typing import Any
from urllib.parse import quote

import httpx


class EventsProviderError(Exception):
    """Базовая ошибка взаимодействия с Events Provider."""


class EventsProviderConfigurationError(EventsProviderError):
    """Ошибка конфигурации клиента."""


class EventsProviderTimeout(EventsProviderError):
    """Истекло время ожидания ответа провайдера."""


class EventsProviderConnectionError(EventsProviderError):
    """Не удалось подключиться к провайдеру."""


class EventsProviderHTTPError(EventsProviderError):
    """Провайдер вернул HTTP-ошибку."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Events Provider returned HTTP {status_code}")


class EventsProviderInvalidResponse(EventsProviderError):
    """Провайдер вернул ответ неожиданного формата."""


class EventsProviderClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key.strip()
        self._owns_http_client = http_client is None

        self._http_client = http_client or httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/",
            timeout=timeout,
            follow_redirects=False,
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not self._api_key:
            raise EventsProviderConfigurationError(
                "Events Provider API key is not configured"
            )

        try:
            response = await self._http_client.request(
                method,
                path,
                headers={"x-api-key": self._api_key},
                **kwargs,
            )
        except httpx.TimeoutException as exc:
            raise EventsProviderTimeout(
                "Events Provider request timed out"
            ) from exc
        except httpx.RequestError as exc:
            raise EventsProviderConnectionError(
                "Could not connect to Events Provider"
            ) from exc

        if not response.is_success:
            raise EventsProviderHTTPError(response.status_code)

        try:
            payload = response.json()
        except ValueError as exc:
            raise EventsProviderInvalidResponse(
                "Events Provider returned invalid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise EventsProviderInvalidResponse(
                "Expected a JSON object from Events Provider"
            )

        return payload

    async def events(
        self,
        changed_at: date,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {
            "changed_at": changed_at.isoformat(),
        }

        if cursor is not None:
            params["cursor"] = cursor

        payload = await self._request_json(
            "GET",
            "api/events/",
            params=params,
        )

        if not isinstance(payload.get("results"), list):
            raise EventsProviderInvalidResponse(
                "Events response must contain a results list"
            )

        next_url = payload.get("next")
        if next_url is not None and not isinstance(next_url, str):
            raise EventsProviderInvalidResponse(
                "Events response contains an invalid next URL"
            )

        return payload

    async def seats(self, event_id: str) -> list[str]:
        payload = await self._request_json(
            "GET",
            f"api/events/{quote(event_id, safe='')}/seats/",
        )

        seats = payload.get("seats")

        if not isinstance(seats, list) or not all(
            isinstance(seat, str) for seat in seats
        ):
            raise EventsProviderInvalidResponse(
                "Seats response must contain a list of strings"
            )

        return seats

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        payload = await self._request_json(
            "POST",
            f"api/events/{quote(event_id, safe='')}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )

        ticket_id = payload.get("ticket_id")

        if not isinstance(ticket_id, str) or not ticket_id:
            raise EventsProviderInvalidResponse(
                "Registration response has no valid ticket_id"
            )

        return ticket_id

    async def unregister(
        self,
        event_id: str,
        ticket_id: str,
    ) -> bool:
        payload = await self._request_json(
            "DELETE",
            f"api/events/{quote(event_id, safe='')}/unregister/",
            json={"ticket_id": ticket_id},
        )

        if payload.get("success") is not True:
            raise EventsProviderInvalidResponse(
                "Unregistration response indicates failure"
            )

        return True

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self._http_client.aclose()
