import logging
from abc import ABC
from datetime import datetime, timedelta
from io import BytesIO
from typing import ClassVar, Optional

from .util import response_handler, request_throttler

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
    last_call: Optional[datetime] = datetime.now() - api_call_interval * 10
    headers: dict[str, str] = {'Content-Type': 'application/json'}

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
    # TODO: re-implement header / param functionality
    api_url: str = 'https://api.thecatapi.com/v1'
    search_image_endpoint: str = '/images/search?format=json'

    @staticmethod
    def _get_image_bytes(url: str):
        response = requests.request(
            method='GET',
            url=url,
        )
        return Image.open(BytesIO(response.content))

    @request_throttler
    def _get_image(self):
        image_url = super()._get(
            url=f"{self.api_url}{self.search_image_endpoint}",
            headers=self.headers,
        )[0]['url']
        return self._get_image_bytes(url=image_url)

    @property
    def cat_images(self) -> Image.Image:

        # TODO:
        #  * fix first skip
        #  * try-catch logic decorator
        #  * throttler decorator
        #  * implement batch logic (api-keys allow 25 images at a time)
        while True:

            try:
                yield self._get_image()
            except Exception as e:  # TODO: figure out how to make less broad
                logger.warning(f"Cat image request failed: {e}.")
                continue

            self.last_call = datetime.now()
