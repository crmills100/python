import requests
import json
import io
import base64
import shutil

from PIL import Image

from moviepy.editor import *

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

from config import Config


config = Config();

URL = config.get_web_service_url();


def create_image(size, prompt, is_new_lyric, text, title, fontsize, path, temp_dir, color="white"):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """
    generate_ai_image(size, prompt, path, is_new_lyric, temp_dir)

    input_image = ImageClip(path)


    components = [input_image]

    # if the title is not provided, use the prompt as the title
#    if (title is None):
#        title = prompt

    x_position = 0
 
    if (title != None):    
        # Create a TextClip with the provided text
        text_clip = TextClip(title, fontsize=fontsize, color=color, method='label', size=size)

        #border_size = 3
        border_clip = TextClip(title, fontsize=fontsize, color='black', method='label', size=size)
    
        x_position = (input_image.w - text_clip.w) // 2 
        y_position = ((input_image.h - text_clip.h) // 2) + (input_image.h // 4)

        text_clip = text_clip.set_position((x_position, y_position))
        border_clip = border_clip.set_position((x_position-1, y_position-1))
    
        components.append(border_clip)
        components.append(text_clip)


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


def generate_ai_image(size, prompt, path, is_new_lyric, temp_dir):
    payload = json.dumps({
        "prompt": prompt,
        "steps": 5,
        "width": size[0],
        "height": size[1],
    })

    temp_path = temp_dir + "temp.png"

    if (not is_new_lyric):
        print(f"generate_ai_image returning image from cache")
        copy_file(temp_path, path)
        return path

    print(f"generate_ai_image generating image")
    print(payload)
  

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", URL, headers=headers, data=payload)

    r = response.json()

    image = Image.open(io.BytesIO(base64.b64decode(r['images'][0])))

    image.save(temp_path)
    copy_file(temp_path, path)

    return path

def copy_file(source_path, destination_path):
    shutil.copyfile(source_path, destination_path)



