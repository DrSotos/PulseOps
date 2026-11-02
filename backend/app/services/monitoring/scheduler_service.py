"""Asynchronous monitoring scheduler service with concurrency throttling and deduplication."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session
from app.models.endpoint import MonitoredEndpoint
from app.services.incidents.detector import process_check_result
from app.services.monitoring.checker import execute_check

logger = get_logger(__name__)

_in_progress: set[str] = set()
_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_CHECKS)
    return _semaphore


async def find_endpoints_due() -> list[MonitoredEndpoint]:
    """Retrieve all active endpoints where elapsed time exceeds the monitoring interval."""
    async with async_session() as session:
        now = datetime.now(UTC)
        stmt = select(MonitoredEndpoint).where(MonitoredEndpoint.is_active == True)
        res = await session.execute(stmt)
        all_active = res.scalars().all()

        due: list[MonitoredEndpoint] = []
        for ep in all_active:
            if ep.last_checked_at is None:
                due.append(ep)
            else:
                elapsed = (now - ep.last_checked_at).total_seconds()
                if elapsed >= ep.monitoring_interval:
                    due.append(ep)
        return due


async def run_single_check(endpoint: MonitoredEndpoint) -> None:
    """Execute a single endpoint health probe with deduplication and semaphore control."""
    ep_key = str(endpoint.id)
    if ep_key in _in_progress:
        return

    _in_progress.add(ep_key)
    sem = _get_semaphore()

    try:
        async with sem:
            # 1. Execute probe
            check = await execute_check(endpoint)

            # 2. Persist check and update endpoint state
            async with async_session() as session:
                session.add(check)

                update_dict = {"last_checked_at": check.completed_at}
                if check.is_successful:
                    update_dict["last_success_at"] = check.completed_at

                await session.execute(
                    update(MonitoredEndpoint)
                    .where(MonitoredEndpoint.id == endpoint.id)
                    .values(**update_dict)
                )
                await session.commit()

                # 3. Incident processing and auto-recovery
                try:
                    await process_check_result(session, endpoint, check)
                except Exception:
                    logger.exception(
                        f"Failed processing incident conditions for {endpoint.name}"
                    )
    except Exception:
        logger.exception(f"Error checking endpoint {endpoint.name}")
    finally:
        _in_progress.discard(ep_key)


async def run_monitoring_cycle() -> None:
    """Scan for due targets and execute concurrent monitoring probes."""
    try:
        due_endpoints = await find_endpoints_due()
        if not due_endpoints:
            return

        logger.debug(f"Executing checks for {len(due_endpoints)} due endpoint(s)")
        tasks = [asyncio.create_task(run_single_check(ep)) for ep in due_endpoints]
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        logger.exception("Error in monitoring cycle")
