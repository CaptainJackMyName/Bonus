"""异步工具函数"""

import asyncio
from typing import Any, Callable, Coroutine, List, TypeVar

T = TypeVar("T")


async def gather_with_limit(
    coroutines: List[Coroutine[Any, Any, T]],
    limit: int = 5,
) -> List[T]:
    """
    并发执行协程列表，限制最大并发数。

    Args:
        coroutines: 协程列表
        limit: 最大并发数

    Returns:
        按输入顺序的结果列表
    """
    if not coroutines:
        return []

    semaphore = asyncio.Semaphore(limit)

    async def _wrap(coro: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*[_wrap(c) for c in coroutines])


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float = 30.0,
    default: T | None = None,
) -> T | None:
    """
    带超时执行协程，超时返回默认值。

    Args:
        coro: 要执行的协程
        timeout: 超时秒数
        default: 超时时的默认返回值

    Returns:
        协程结果或默认值
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return default


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    在同步上下文中运行异步协程。
    适用于 Flet 事件回调中需要调用异步函数的场景。
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
