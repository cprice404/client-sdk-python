# import asyncio
# from typing import Awaitable, TypeVar
# import threading
#
# _TReturn = TypeVar("_TReturn")
# T = TypeVar("T")
#
#
#
# def _start_background_loop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()
#
# _LOOP = asyncio.new_event_loop()
# _LOOP_THREAD = threading.Thread(
#     target=_start_background_loop, args=(_LOOP,), daemon=True
# )
# _LOOP_THREAD.start()
#
# def asyncio_run(coro: Awaitable[T], timeout=30) -> T:
#     """
#     Runs the coroutine in an event loop running on a background thread,
#     and blocks the current thread until it returns a result.
#     This plays well with gevent, since it can yield on the Future result call.
#
#     :param coro: A coroutine, typically an async method
#     :param timeout: How many seconds we should wait for a result before raising an error
#     """
#     print("Calling threadsafe")
#     future = asyncio.run_coroutine_threadsafe(coro, _LOOP)
#     print("Got future")
#     result = future.result(timeout=timeout)
#     print("Got future result")
#     return result
#     # return asyncio.run_coroutine_threadsafe(coro, _LOOP).result(timeout=timeout)
#
#
# # NOTES:
# #
# # 1. it would be really nice to put some more meaningful type hints here but I'm not familiar
# #    enough with asyncio / coroutines to understand their types.
# # 2. Kenny believes that we should be able to do this without a direct dependency on asyncio,
# #    by writing a loop that calls `send` on the coroutine and then returns on StopIteration.
# #    I was not able to get this working during my timeboxed window so left it like this for now.
# def wait_for_coroutine(loop: asyncio.AbstractEventLoop, coroutine: Awaitable[_TReturn], ) -> _TReturn:
#     print("WAITING FOR COROUTINE")
#     return asyncio_run(coroutine)
#     # print("Calling threadsafe")
#     # future = asyncio.run_coroutine_threadsafe(coroutine(), loop)
#     # print("Got future")
#     # result = future.result()
#     # print("Got future result")
#     # return result
#
