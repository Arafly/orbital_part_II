from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Optional

from app.clients import OrbitalClient, ReportNotFoundError
from app.credits import calculate_credits, quantize_2dp
from app.schemas import Message, UsageItem, UsageResponse

class UsageService:
    def __init__(self, client: OrbitalClient, report_concurrency_limit: int = 5) -> None:
        self.client = client
        self.report_concurrency_limit = report_concurrency_limit

    async def _resolve_reports(
        self, report_ids: set[int]
    ) -> dict[int, Optional[tuple[str, Decimal]]]:
        semaphore = asyncio.Semaphore(self.report_concurrency_limit)
        cache: dict[int, Optional[tuple[str, Decimal]]] = {}

        async def fetch_one(report_id: int) -> None:
            async with semaphore:
                try:
                    report = await self.client.fetch_report(report_id)
                    cache[report_id] = (report.name, quantize_2dp(report.credit_cost))
                except ReportNotFoundError:
                    cache[report_id] = None

        await asyncio.gather(*(fetch_one(rid) for rid in report_ids))
        return cache

    async def build_usage(self) -> UsageResponse:
        messages = await self.client.fetch_messages()
        unique_report_ids = {msg.report_id for msg in messages if msg.report_id is not None}
        report_cache = await self._resolve_reports({rid for rid in unique_report_ids if rid is not None})

        usage_items: list[UsageItem] = []

        for message in messages:
            report_name: Optional[str] = None
            credits: Decimal

            if message.report_id is not None and message.report_id in report_cache:
                cached = report_cache[message.report_id]
                if cached is not None:
                    report_name, credits = cached
                else:
                    credits = calculate_credits(message.text)
            else:
                credits = calculate_credits(message.text)

            usage_items.append(
                UsageItem(
                    message_id=message.id,
                    timestamp=message.timestamp.isoformat().replace("+00:00", "Z"),
                    report_name=report_name,
                    credits_used=float(credits),
                )
            )

        return UsageResponse(usage=usage_items)