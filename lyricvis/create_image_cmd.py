import create_image_sd
import argparse
import tempfile


SIZE_VGA = (640, 480)
FONTSIZE=30

size = SIZE_VGA
prompt = "A computer bored with computation"
is_new_lyric = True
text = " "
title = "NOT USED"
fontsize = FONTSIZE
path = "out.png"
temp_dir = tempfile.gettempdir()
color = "#76B900"


parser = argparse.ArgumentParser()
parser.add_argument("--prompt", help="prompt for AI to generate image")
parser.add_argument("--text", help="text to overlay onto the image")
parser.add_argument("--path", help="path of the image to generate, defaults to out.png")
parser.add_argument("--temp_dir", help="path of the image to generate, defaults to system temp directory")
parser.add_argument("--color", help="color represented in hex string: #RRGGBB or name of color (ex 'red')")


args = parser.parse_args()

if (args.prompt):
    prompt = args.prompt

if (args.text):
    text = args.text

if (args.path):
    path = args.path

if (args.temp_dir):
    temp_dir = args.temp_dir

if (args.color):
    color = args.color


print(f"generating image: {size}, {prompt}, {is_new_lyric}, {text}, {title}, {fontsize}, {path}, {temp_dir}, {color}")

create_image_sd.create_image(size, prompt, is_new_lyric, text, title, fontsize, path, temp_dir, color)
