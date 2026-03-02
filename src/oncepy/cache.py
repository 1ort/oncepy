import asyncio
from collections.abc import Callable, Coroutine, Hashable
from typing import (
    Any,
    ParamSpec,
    TypeVar,
)

P = ParamSpec("P")
R = TypeVar("R")
K = TypeVar("K", bound=Hashable)


class OnceCache:
    """
    single lock OnceMap/singleflight for asyncio: key -> shared Task.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._tasks: dict[Hashable, asyncio.Task[Any]] = {}

    async def clear(self, *, cancel_inflight: bool = False) -> None:
        async with self._lock:
            tasks = list(self._tasks.values())
            self._tasks.clear()

        if cancel_inflight:
            for t in tasks:
                t.cancel()

    async def invalidate(self, key: Hashable, *, cancel_inflight: bool = False) -> bool:
        async with self._lock:
            task = self._tasks.pop(key, None)

        if task is None:
            return False

        if cancel_inflight:
            task.cancel()
        return True

    async def run_once(
        self,
        key: Hashable,
        work: Callable[[], Coroutine[Any, Any, R]],
        *,
        cache_exceptions: bool = True,
    ) -> R:
        async with self._lock:
            existing = self._tasks.get(key)
            if existing is not None:
                task: asyncio.Task[R] = existing
            else:
                task = asyncio.create_task(work())
                self._tasks[key] = task

                def _done_callback(t: asyncio.Task[R]) -> None:
                    # 1) Remove warning "Task exception was never retrieved"
                    if not t.cancelled():
                        _ = t.exception()

                    # 2) cleanup
                    remove = t.cancelled() or t.exception() is not None and not cache_exceptions
                    if remove and key in self._tasks:
                        self._tasks.pop(key, None)

                task.add_done_callback(_done_callback)

        return await asyncio.shield(task)
