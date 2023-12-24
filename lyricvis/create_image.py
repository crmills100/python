from moviepy.editor import *

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})



def create_image(size, prompt, fontsize, path):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """

    print("Hello from a create_image: ", size, prompt, path)


    text_clip = TextClip(txt=prompt, size=size, fontsize=fontsize, font="Lane", color="black", bg_color="white")

    text_clip.save_frame(path);










