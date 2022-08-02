import functools
import logging
from abc import ABC
from datetime import datetime, timedelta
from io import BytesIO
from time import sleep
from typing import Callable, ClassVar, Optional, Union

import requests
from PIL import Image
from pydantic import BaseModel

logging.basicConfig(
    level="INFO",
    format="%(levelname)s::%(name)s::%(asctime)s::%(message)s",
)
logger = logging.getLogger(__name__)


class ApiClient(BaseModel):
    api_call_interval: ClassVar[timedelta] = timedelta(seconds=3)

    api_url: str
    api_key: Optional[str]
    last_call: Optional[datetime]

    @staticmethod
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

    @staticmethod
    @response_handler
    def _get(
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> requests.Response:
        response = requests.request(
            method='GET',
            url=url,
            headers=headers,
            params=params,
            data=data,
        )
        return response


class CatImageGenerator(ApiClient, ABC):
    api_url: str = 'https://api.thecatapi.com/v1'
    search_image_endpoint: str = '/images/search?format=json'

    @staticmethod
    def _get_image_bytes(url: str):
        response = requests.request(
            method='GET',
            url=url,
        )
        return Image.open(BytesIO(response.content))

    def get_cat_images(self) -> Image.Image:
        headers = {'Content-Type': 'application/json'}
        if self.api_key is not None:
            headers['x-api-key'] = self.api_key
        # this is to exclude gifs, because they provide most peculiar results
        # in case api-key header is not provided, this param does not take action
        params = {'mime_types': 'png,jpg'}

        # TODO:
        #  * fix first skip
        #  * try-catch logic decorator
        #  * throttler decorator
        #  * implement batch logic (api-keys allow 25 images at a time)
        self.last_call = datetime.now() - self.api_call_interval * 10
        while True:
            try:
                if (self.last_call + self.api_call_interval) < datetime.now():
                    logger.info(f"Skipping iteration on cat images generator.")
                    pass
                else:
                    sleep(self.api_call_interval.total_seconds())

                image_url = super()._get(
                    url=f"{self.api_url}{self.search_image_endpoint}",
                    headers=headers,
                    params=params,
                )[0]['url']
                image = self._get_image_bytes(url=image_url)

                self.last_call = datetime.now()

                yield image
            except Exception as e:  # TODO: figure out how to make less broad
                logger.warning(f"Cat image request failed: {e}.")
                continue
