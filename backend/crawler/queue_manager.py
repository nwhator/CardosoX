"""Async worker queue with visited URL cache and retry bookkeeping."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class CrawlJob:
    url: str
    depth: int = 0
    attempts: int = 0


class QueueManager:
    def __init__(self):
        self.queue: asyncio.Queue[CrawlJob] = asyncio.Queue()
        self.visited: set[str] = set()

    async def add(self, url: str, depth: int = 0, attempts: int = 0) -> bool:
        if url in self.visited:
            return False
        self.visited.add(url)
        await self.queue.put(CrawlJob(url=url, depth=depth, attempts=attempts))
        return True

    async def get(self) -> CrawlJob:
        return await self.queue.get()

    def task_done(self) -> None:
        self.queue.task_done()

    async def join(self) -> None:
        await self.queue.join()

