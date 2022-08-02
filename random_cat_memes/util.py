import functools
from typing import Callable, Optional, Union


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
