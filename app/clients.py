from __future__ import annotations

from decimal import Decimal
from typing import Optional

import httpx

from app.schemas import Message, MessageResponse, ReportResponse

MESSAGES_URL = "https://owpublic.blob.core.windows.net/tech-task/messages/current-period"
REPORT_URL_TEMPLATE = "https://owpublic.blob.core.windows.net/tech-task/reports/{report_id}"


class UpsteamServerError(Exception):
    pass

class ReportNotFoundError(Exception):
    pass

class OrbitalClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client

    async def fetch_messages(self) -> list[Message]:
        response = await self.http_client.get(MESSAGES_URL)

        if response.status_code != 200:
            raise UpsteamServerError(f"Failed to fetch messages: {response.status_code}")
        payload = MessageResponse.model_validate(response.json())
        return payload.messages

    async def fetch_report(self, report_id: int) -> ReportResponse:
        url = REPORT_URL_TEMPLATE.format(report_id=report_id)
        response = await self.http_client.get(url)

        if response.status_code == 404:
            raise ReportNotFoundError(f"Report with id {report_id} not found")

        if response.status_code != 200:
            raise UpsteamServerError(f"Failed to fetch report {report_id}: HTTP {response.status_code}")

        return ReportResponse.model_validate(response.json())