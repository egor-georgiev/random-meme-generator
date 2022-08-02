import os
from collections import namedtuple
from typing import ClassVar, TypeVar

from PIL import ImageDraw, ImageFont
from PIL.Image import Image
from pydantic import BaseModel, validator

TextPosition = namedtuple('TextPosition', ['x', 'y'])
Font = namedtuple('Font', ['font_obj', 'font_size'])


# TODO
#   * enrich logging

class MemeGenerator(BaseModel):
    fg_color: ClassVar[tuple[int, int, int]] = (255, 255, 255)
    bg_color: ClassVar[tuple[int, int, int]] = (0, 0, 0)
    border_width: ClassVar[int] = 2

    top_text: str
    bottom_text: str
    image: Image
    font_path: str

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
    def font(self) -> Font:
        font_size = self.image_width // 6

        longest_text = self.top_text if (len(self.top_text) > len(self.bottom_text)) else self.bottom_text
        text_length = ImageFont.truetype(self.font_path, font_size).getlength(longest_text)

        max_text_length = self.image_width - self.no_text_margin

        if text_length > max_text_length:
            font_size *= max_text_length / text_length

        return Font(font_obj=ImageFont.truetype(self.font_path, int(font_size)), font_size=int(font_size))

    @property
    def top_text_position(self) -> TextPosition:
        x = (self.image.size[0] / 2) - int(self.font.font_obj.getlength(self.top_text) / 2)
        y = 0
        return TextPosition(x=x, y=y)

    @property
    def bottom_text_position(self) -> TextPosition:
        # TODO: simplify
        x = (self.image_width / 2) - (self.font.font_obj.getlength(self.bottom_text) / 2)
        y = self.image_height - self.font.font_obj.getbbox(self.bottom_text)[3] - self.no_text_margin
        return TextPosition(x=x, y=y)

    def _draw_text(self, position, text, color) -> None:
        draw = ImageDraw.Draw(self.image)
        try:
            draw.text(xy=position, text=text, fill=color, font=self.font.font_obj, align='center')
        except TypeError as e:
            # this error happens when we get a black-and-white image
            if 'color must be int or single-element tuple' in repr(e):
                draw.text(xy=position, text=text, fill=set(color).pop(), font=self.font.font_obj, align='center')
            else:
                raise e

    def _draw_bg_text(self, text: str, text_position: TextPosition) -> None:

        x = text_position.x
        y = text_position.y

        n = self.border_width  # readability
        for position in (x - n, y - n), (x + n, y - n), (x - n, y + n), (x + n, y + n):
            self._draw_text(position, text, color=self.bg_color)

    def _draw_fg_text(self, text: str, text_position: TextPosition) -> None:
        self._draw_text(text_position, text, color=self.fg_color)

    def generate_meme(self) -> None:
        # TODO: loop-de-loop
        self._draw_bg_text(text=self.top_text, text_position=self.top_text_position)
        self._draw_fg_text(text=self.top_text, text_position=self.top_text_position)
        self._draw_bg_text(text=self.bottom_text, text_position=self.bottom_text_position)
        self._draw_fg_text(text=self.bottom_text, text_position=self.bottom_text_position)
