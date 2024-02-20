import requests
import json
import io
import base64
from PIL import Image

from moviepy.editor import *

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})

from config import Config

config = Config();

URL = config.get_web_service_url();
SIZE_VGA = (640, 480)


def create_image(size, prompt, is_new_lyric, text, fontsize, path):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """
    generate_ai_image(size, prompt, path)

    input_image = ImageClip(path)

    # Create a TextClip with the provided text
    text_clip = TextClip(prompt, fontsize=fontsize, color="white", method='label', size=size)

    #border_size = 3
    border_clip = TextClip(prompt, fontsize=fontsize, color='black', method='label', size=size)
    
    x_position = (input_image.w - text_clip.w) // 2 
    y_position = (input_image.h - text_clip.h) // 2

    text_clip = text_clip.set_position((x_position, y_position))
    border_clip = border_clip.set_position((x_position-1, y_position-1))
    components = [input_image, border_clip, text_clip];

    

    # add any additional text
    if (text != None):
        additional_clip = TextClip(text, fontsize=(fontsize - 2), color="white", method='label', size=size)
        print(input_image.h)
        y_position = (input_image.h / 2) - 30
        additional_clip = additional_clip.set_position((x_position, y_position))
        components.append(additional_clip)


    # Write text onto the input image
    #final_clip = input_image.copy().add_mask().blit(text_clip.on_color(size=input_image.size).set_pos((x_position, y_position)))
    final_clip = CompositeVideoClip(components)

    final_clip.save_frame(path)


    return path


def generate_ai_image(size, prompt, path):
    payload = json.dumps({
        "prompt": prompt,
        "steps": 5,
        "width": size[0],
        "height": size[1],
    })

    print(payload)
  

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", URL, headers=headers, data=payload)

    r = response.json()

    image = Image.open(io.BytesIO(base64.b64decode(r['images'][0])))

    image.save(path)

    return path

#create_image(SIZE_VGA, "ultra realistic close up portrait ((beautiful pale cyberpunk female with heavy black eyeliner))", 20, "foo.png")

