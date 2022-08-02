import os
from collections import namedtuple
from typing import ClassVar

from PIL import ImageDraw, ImageFont
from PIL.Image import Image
from pydantic import BaseModel, validator

# TODO
#   * centralized settings

TextPosition = namedtuple('TextPosition', ['x', 'y'])


class MemeGenerator(BaseModel):
    fg_color: ClassVar[tuple[int, int, int]] = (255, 255, 255)
    bg_color: ClassVar[tuple[int, int, int]] = (0, 0, 0)

    top_text: str
    bottom_text: str
    image: Image
    font_path: str
    border_width: int = 2  # TODO: use proportion

    class Config:
        arbitrary_types_allowed = True  # PIL.Image.Image

    @validator('font_path')
    def font_exists(cls, value: str) -> str:
        if os.path.exists(value):
            return value
        raise ValueError

    @property
    def image_width(self) -> int:
        return self.image.size[0]

    @property
    def image_height(self) -> int:
        return self.image.size[1]

    @property
    def no_text_margin(self) -> float:
        if self.image_width > self.image_height:
            return 0.03 * self.image_width
        return 0.03 * self.image_height

    @property
    def font(self) -> ImageFont:
        font_size = self.image_width // 6

        longest_text = max(self.top_text, self.bottom_text, key=len)
        longest_text_width = ImageFont.truetype(self.font_path, font_size).getlength(longest_text)
        max_text_width = self.image_width - self.no_text_margin

        if longest_text_width > max_text_width:
            font_size = int(font_size * max_text_width / longest_text_width)

        return ImageFont.truetype(self.font_path, font_size)

    @property
    def top_text_position(self) -> TextPosition:
        x = (self.image_width - self.font.getlength(self.top_text)) // 2
        y = 0
        return TextPosition(x=x, y=y)

    @property
    def bottom_text_position(self) -> TextPosition:
        x = (self.image_width - self.font.getlength(self.bottom_text)) // 2
        y = self.image_height - self.font.getbbox(self.bottom_text)[3] - self.no_text_margin
        return TextPosition(x=x, y=y)

    def _draw_text(self, position, text, color) -> None:
        draw = ImageDraw.Draw(self.image)
        try:
            draw.text(xy=position, text=text, fill=color, font=self.font, align='center')
        except TypeError as te:
            if 'color must be int or single-element tuple' in repr(te):
                # this error happens when we get a black-and-white image
                # TODO: a property to determine, whether an image is greyscale or no
                draw.text(xy=position, text=text, fill=set(color).pop(), font=self.font, align='center')
            else:
                raise te
        except ValueError as ve:
            if 'cannot allocate more than 256 colors' in repr(ve):
                # TODO: use any existing colors closest to fg and bg colors
                raise NotImplementedError(
                    'Encountered a gif with 256 colors, but no bg or fg color. Not handling.'
                )
            else:
                raise ve

    def _draw_bg_text(self, text: str, text_position: TextPosition) -> None:
        x, y = text_position.x, text_position.y
        n = self.border_width  # readability

        for position in (x - n, y - n), (x + n, y - n), (x - n, y + n), (x + n, y + n):
            self._draw_text(position, text, color=self.bg_color)

    def _draw_fg_text(self, text: str, text_position: TextPosition) -> None:
        self._draw_text(text_position, text, color=self.fg_color)

    def generate_meme(self) -> None:
        for text, position in zip(
                (self.top_text, self.bottom_text), (self.top_text_position, self.bottom_text_position)
        ):
            self._draw_bg_text(text=text, text_position=position)
            self._draw_fg_text(text=text, text_position=position)
        # TODO: return
