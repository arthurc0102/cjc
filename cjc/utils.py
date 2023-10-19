import asyncio
import functools
import typing as t

RT = t.TypeVar("RT")


def async_to_sync(
    f: t.Callable[..., t.Coroutine[t.Any, t.Any, RT]],
) -> t.Callable[..., RT]:
    @functools.wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> RT:
        return asyncio.run(f(*args, **kwargs))

    return wrapper
