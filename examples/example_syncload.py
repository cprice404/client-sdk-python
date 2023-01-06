import logging
import os

import colorlog
from momento.logs import initialize_momento_logging
from momento.simple_cache_client import SimpleCacheClient


def initialize_logging(level: int) -> None:
    initialize_momento_logging()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(thin_cyan)s%(name)s%(reset)s %(message)s"
        )
    )
    handler.setLevel(level)
    root_logger.addHandler(handler)


def main():
    initialize_logging(logging.DEBUG)
    logger = logging.getLogger("load-gen")
    logger.info("Hello world")
    auth_token = os.getenv("MOMENTO_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("Missing required environment variable MOMENTO_AUTH_TOKEN")
    cache_name = "python-loadgen"
    cache_value = "x" * 1_000
    with SimpleCacheClient(
        auth_token=auth_token,
        default_ttl_seconds=60,
        request_timeout_ms=5_000,
    ) as client:
        for i in range(1_000_000):
            if i % 1_000 == 0:
                logger.info(f"Performing a set ({i})")
            client.set(cache_name, key="foo", value=cache_value)
            if i % 1_000 == 0:
                logger.info(f"Performing a get ({i})")
            result = client.get(cache_name, key="foo")
            # logger.info(result)


if __name__ == "__main__":
    main()