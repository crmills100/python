from moviepy.editor import *

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})

import shutil

def create_image(size, prompt, fontsize, path):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """

    print("Hello from a create_image: ", size, prompt, path)


    text_clip = TextClip(txt=prompt, size=size, fontsize=fontsize, font="Lane", color="white", bg_color="black")

    text_clip.save_frame(path)

    return path


def create_blank(size, path):
    text_clip = TextClip(txt=" ", size=size, fontsize=10, font="Lane", color="white", bg_color="black")

    text_clip.save_frame(path)

    return path

def copy_file(source_path, destination_path):
    shutil.copyfile(source_path, destination_path)

