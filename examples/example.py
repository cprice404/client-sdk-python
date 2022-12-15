import asyncio
import logging
import os
import threading
import time

import aiohttp

from example_utils.example_logging import initialize_logging

import momento.errors as errors
import momento.simple_cache_client as scc

_MOMENTO_AUTH_TOKEN = os.getenv("MOMENTO_AUTH_TOKEN")
_CACHE_NAME = "cache"
_ITEM_DEFAULT_TTL_SECONDS = 60
_KEY = "MyKey"
_VALUE = "MyValue"

_logger = logging.getLogger("momento-example")


def _print_start_banner() -> None:
    _logger.info("******************************************************************")
    _logger.info("*                      Momento Example Start                     *")
    _logger.info("******************************************************************")


def _print_end_banner() -> None:
    _logger.info("******************************************************************")
    _logger.info("*                       Momento Example End                      *")
    _logger.info("******************************************************************")


def _create_cache(cache_client: scc.SimpleCacheClient, cache_name: str) -> None:
    try:
        cache_client.create_cache(cache_name)
    except errors.AlreadyExistsError:
        _logger.info(f"Cache with name: {cache_name!r} already exists.")


def _list_caches(cache_client: scc.SimpleCacheClient) -> None:
    _logger.info("Listing caches:")
    list_cache_result = cache_client.list_caches()
    while True:
        for cache_info in list_cache_result.caches():
            _logger.info(f"- {cache_info.name()!r}")
        next_token = list_cache_result.next_token()
        if next_token is None:
            break
        list_cache_result = cache_client.list_caches(next_token)
    _logger.info("")

def thread_function(name, cache_client):
    logging.info("Thread %s: starting", name)

    for index in range(1000):
        _logger.info(f"Setting Key: {_KEY!r} Value: {_VALUE!r}")
        cache_client.set(_CACHE_NAME, _KEY, _VALUE)

        _logger.info(f"Getting Key: {_KEY!r}")
        get_resp = cache_client.get(_CACHE_NAME, _KEY)
        _logger.info(f"Look up resulted in a : {str(get_resp.status())}")
        _logger.info(f"Looked up Value: {str(get_resp.value())!r}")
    logging.info("Thread %s: finishing", name)


async def aiohttp_function():
    async with aiohttp.ClientSession() as session:
        for index in range(500):
            async with session.get('https://python.org') as response:
                print("Status:", response.status)
                print("Content-type:", response.headers['content-type'])

                html = await response.text()
                print("Body:", html[:15], "...")


async def main():
    initialize_logging()
    _print_start_banner()
    with scc.SimpleCacheClient(_MOMENTO_AUTH_TOKEN, _ITEM_DEFAULT_TTL_SECONDS) as cache_client:
        _create_cache(cache_client, _CACHE_NAME)
        _list_caches(cache_client)

        threads = list()
        for index in range(100):
            logging.info("Main    : create and start thread %d.", index)
            x = threading.Thread(target=thread_function, args=(index,cache_client))
            threads.append(x)
            x.start()
        #
        # aiohttp_thread = threading.Thread(target=aiohttp_function)
        # threads.append(aiohttp_thread)
        # aiohttp_thread.start()

        # aiohttp_coro = aiohttp_function()

        for index, thread in enumerate(threads):
            logging.info("Main    : before joining thread %d.", index)
            thread.join()
            logging.info("Main    : thread %d done", index)

        # print("Threads done, awaiting aiohttp coro")
        # await aiohttp_coro
        print("Done done.")

if __name__ == "__main__":
    main()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    _print_end_banner()
