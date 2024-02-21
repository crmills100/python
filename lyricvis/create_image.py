from moviepy.editor import *

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})

import shutil
import os


def create_image(size, prompt, fontsize, path):
    """ create an image of dimensions size(width, height)) based on the text prompt, write the image to the path
    
    """

    print("Hello from a create_image: ", size, prompt, path)


    text_clip = TextClip(txt=prompt, size=size, fontsize=fontsize, font="Lane", color="white", bg_color="black")

    text_clip.save_frame(path)

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
    print(f"There are ", len(image_files), " image files")
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

