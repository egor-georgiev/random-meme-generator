import os
import shutil
import sqlite3

from random_cat_memes.clients import CatImageGenerator
from random_cat_memes.memegenerator import MemeGenerator


def cleanup():
    try:
        shutil.rmtree('out')
    except FileNotFoundError:
        pass
    os.mkdir('out')


def get_random_meme_text():
    con = sqlite3.connect('memetext.db')
    cur = con.cursor()

    res = cur.execute('SELECT * FROM memetext ORDER BY RANDOM() LIMIT 1;')
    return res.fetchone()


if __name__ == '__main__':
    cleanup()

    n = 0
    cat_api = CatImageGenerator()
    for image in cat_api.cat_images:  # noqa
        if n > 500:
            break

        top_text, bottom_text = get_random_meme_text()
        memegen = MemeGenerator(
            top_text=top_text,
            bottom_text=bottom_text,
            image=image,
            font_path='fonts/impact.ttf',
        )
        image = memegen.generate_meme()
        image.save(f'out/test{n}.png')
        n += 1
