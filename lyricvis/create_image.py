
from config import Config
config = Config();

from moviepy.editor import *
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": config.get_imagemagick_binary()})

import shutil
import os


def create_image3(size, prompt, title, fontsize, path):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """

    print("Hello from a create_image: ", size, prompt, fontsize, path)

    return create_image(size, prompt, True, None, title, fontsize, path, None, color="white")

#    text_clip = TextClip(txt=prompt, size=size, fontsize=fontsize, font="Lane", color="white", bg_color="black")
#
#    text_clip.save_frame(path)
#
#    return path

def create_image(size, prompt, is_new_lyric, text, title, fontsize, path, temp_dir, color="white"):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """

    # Create a TextClip with the provided text
    print("create_image: size:", size, "prompt:", prompt, "is_new_lyric:", is_new_lyric, "text:", text, "title:", title, "fontsize:", fontsize, "path", path, "temp_dir", temp_dir, "color:", color)
    if (prompt == None):
        prompt = " "
    
    text_clip = TextClip(prompt, fontsize=fontsize, color=color, method='label', size=size)
    #text_clip = TextClip("foo", fontsize=fontsize, color="white", method='label', size=size)

    print("text_clip values: ", size, text_clip.w, text_clip.h, prompt)
    #border_size = 3
    border_clip = TextClip(prompt, fontsize=fontsize, color='black', method='label', size=size)
    
    x_position = 0 
    y_position = 0 + (text_clip.h // 4)

    text_clip = text_clip.set_position((x_position, y_position))
    border_clip = border_clip.set_position((x_position-1, y_position-1))
    components = [border_clip, text_clip];


    # add any additional text
    if (text != None):
        additional_clip = TextClip(text, fontsize=(fontsize - 2), color="white", method='label', size=size)
        y_position = (text_clip.h / 2) - 30
        additional_clip = additional_clip.set_position((x_position, y_position))
        components.append(additional_clip)

   # add any additional title
    if (title != None):
        additional_clip = TextClip(title, fontsize=(fontsize - 2), color="#9616CC", method='label', size=size)
        y_position = 30
        additional_clip = additional_clip.set_position((x_position, y_position))
        components.append(additional_clip)



    # Write text onto the input image
    #final_clip = input_image.copy().add_mask().blit(text_clip.on_color(size=input_image.size).set_pos((x_position, y_position)))
    final_clip = CompositeVideoClip(components)

    final_clip.save_frame(path)


    return path


def create_transparent_image(size, prompt, fontsize, path):
    # Create a TextClip with transparent background

    print("Hello from a create_transparent_image: ", size, prompt, path)

    text_clip = TextClip(txt=prompt, size=size, fontsize=fontsize, font="Lane", color="white", bg_color="transparent")

    text_clip.save_frame(path)
    
    return path




def create_blank(size, path):
    text_clip = TextClip(txt=" ", size=size, fontsize=10, font="Lane", color="white", bg_color="black")

    text_clip.save_frame(path)

    return path


def overlay_images(background_path, overlay_path, output_path):
    # Load images
    background = ImageClip(background_path)
    overlay = ImageClip(overlay_path)

    # Ensure both images have the same dimensions
    width = max(background.size[0], overlay.size[0])
    height = max(background.size[1], overlay.size[1])

    background = background.resize((width, height))
    overlay = overlay.resize((width, height))

    # Overlay one image over the other
    overlayed_clip = CompositeVideoClip([background, overlay.set_position('center')])

    # Write the overlayed image to a file
    overlayed_clip.to_ImageClip().save_frame(output_path)

    print(f"Images overlayed and saved to {output_path}")

def copy_file(source_path, destination_path):
    shutil.copyfile(source_path, destination_path)


def create_video(image_root_path, fps, audio_path, output_path, length):
    print(f"create_video {image_root_path} {fps}, {output_path}")


    # List all files in the directory
    image_files = [f for f in os.listdir(image_root_path) if f.endswith(('.png'))]
        
    # Sort image files by name (assuming the file names represent the order)
    image_files.sort()
    print(f"There are", len(image_files), "image files")
    if (len(image_files) != length):
        print(f"len(image_files) != length")
        exit(-1)
        
    # Create ImageSequenceClip
    clip = ImageSequenceClip([os.path.join(image_root_path, f) for f in image_files], fps=fps)
        
    # Add audio to the video
    audio = AudioFileClip(audio_path).subclip(0, len(image_files) / fps)
    video_with_audio = clip.set_audio(audio)

    # Write the video file
    video_with_audio.write_videofile(output_path)

