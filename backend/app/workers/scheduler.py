"""Standalone PulseOps Monitoring Worker process.

Continuously scans and monitors endpoints independently of user dashboard sessions.
Run with: python -m app.workers.scheduler
"""

from __future__ import annotations

import asyncio
import signal
import sys

from app.core.config import settings
from app.core.logging import get_logger
from app.services.monitoring.scheduler_service import run_monitoring_cycle

logger = get_logger("pulseops.worker")

_is_running = True


def _signal_handler(signum, frame):
    global _is_running
    logger.info(f"Signal {signum} received, stopping monitoring worker gracefully...")
    _is_running = False


async def start_worker_loop():
    logger.info("Starting PulseOps Monitoring Worker Engine...")
    logger.info(f"Max Concurrent Checks: {settings.MAX_CONCURRENT_CHECKS}")
    logger.info(f"Private Network Probes Allowed: {settings.ALLOW_PRIVATE_NETWORKS}")

    while _is_running:
        try:
            await run_monitoring_cycle()
        except Exception:
            logger.exception("Cycle execution failure")

        # Responsive sleep loop allowing quick shutdown
        for _ in range(5):
            if not _is_running:
                break
            await asyncio.sleep(1)

    logger.info("PulseOps Monitoring Worker Engine stopped cleanly.")


def run():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        asyncio.run(start_worker_loop())
    except KeyboardInterrupt:
        logger.info("Worker process terminated by user interrupt.")
        sys.exit(0)


if __name__ == "__main__":
    run()

