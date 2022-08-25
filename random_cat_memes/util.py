import functools
import logging
from datetime import datetime
from time import sleep
from typing import Callable, Optional, Union

logging.basicConfig(
    level="INFO",
    format="%(levelname)s::%(name)s::%(asctime)s::%(message)s",
)
logger = logging.getLogger(__name__)


def response_handler(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Optional[Union[list, dict]]:
        response = func(*args, **kwargs)
        if response.status_code < 400:
            if response.text:
                return response.json()
        else:
            raise Exception(f"Response status: {response.status_code}, message: {None}")
        return None

    return wrapper


def request_throttler(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # TODO: hint
        # expect class instance as 0th argument
        last_call = args[0].last_call
        api_call_interval = args[0].api_call_interval

        # TODO: calculate for how long to sleep
        # TODO: check whether calculation is correct
        if (last_call + api_call_interval) > datetime.now():
            logger.warning('Throttling api calls.')
            sleep(api_call_interval.total_seconds())
        args[0].last_call = datetime.now()
        return func(*args, **kwargs)

    return wrapper


def infinite_generator(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                resu
                yield self._get_image()
            except Exception as e:  # TODO: figure out how to make less broad
                logger.warning(f"Cat image request failed: {e}.")
                continue

    return wrapper

