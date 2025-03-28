from song import Song
import create_image
import create_image_sd
import os
import argparse


SIZE_VGA = (640, 480)
SIZE_720 = (1280, 720)
SIZE_VIDEO = SIZE_VGA
FONTSIZE=20
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\"
IMAGE_TEMP_DIR = "C:\\temp\\lyric_vis\\temp\\"
BLANK_IMAGE_PATH = IMAGE_TEMP_DIR + "blank_640x480.png"

GEN_IMAGES = True

FPS = 30
SECS_PER_WORD = 2
MAX_FRAMES = 100000


SONG_FILE_PATH = ""
TARGET_VIDEO_PATH = ""
MODE_VIDEO = 'Text' # 'Text' or 'Image'

parser = argparse.ArgumentParser()
parser.add_argument("--song_file", help="path to JSON file with metadata and lyrics", required=True)
parser.add_argument("--path", help="filename path to save generated video file to", required=True)
parser.add_argument("--mode", help="'text' or 'image' mode")

args = parser.parse_args()


if (args.song_file):
    song_file_path = args.song_file

if (args.path):
    TARGET_VIDEO_PATH = args.path

if (args.mode):
    MODE_VIDEO = "Image" if args.mode.lower() == "image" else "Text"



class FrameInfo:
    def __init__(self, num, prompt, text, title, graphic_path):
        self.num = num
        self.prompt = prompt
        self.text = text
        self.title = title
        self.graphic_path = graphic_path

    def __str__(self):
        return f"FrameInfo(num='{self.num}', prompt='{self.prompt}', text='{self.text}', title='{self.title}', graphic_path='{self.graphic_path}')"


def format_number(integer):
    formatted_str = str(integer).zfill(5)
    return formatted_str

def count_words(lyric):
    if lyric is None or not lyric.strip():
        return 0  # Return 0 for null strings or strings with only whitespace
    else:
        # Split the string by spaces
        words = lyric.split()
        # Return the length of the resulting list
        return len(words)

def timestamp_to_frames(timestamp):
    hours, minutes, seconds = map(int, timestamp.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    frames_per_second = FPS
    frames = total_seconds * frames_per_second
    return frames

def add_blank_frame(frame_info, frame_number, count):
    print(f"add_blank_frame: {frame_number}, {count}")

    for x in range(0, count):
        frame_info.append(FrameInfo(frame_number + x, None, None, None, None))

def add_frame(frame_info, frame_number, count, lyric, prompt):
    print(f"add_frame: {frame_number}, {count}, {lyric}, {prompt}")
    if prompt == None:
        prompt = lyric

    if (lyric is None):
        add_blank_frame(frame_info, frame_number, count)
        return

    for x in range(0, count):
        frame_info.append(FrameInfo(frame_number + x, prompt, None, lyric, None))

def add_title(frame_info, title, frame_number, count):
    print(f"add_title: {frame_number}, {count}, {title}")
    for x in range(0, count):
        idx = frame_number + x
        frame = frame_info[frame_number + x]
        frame.title = title
        #frame_info.append(FrameInfo(frame_number + x, None, None, None, title))


def add_credit(frame_info, credit, frame_number, count):
    print(f"add_credit: {frame_number}, {count}, {credit}")
    for x in range(0, count):
        idx = frame_number + x
        frame = frame_info[frame_number + x]
        for key, value in credit.items():
            if (key == ""):
                frame.text = value
            else:
                frame.text = key + ": " + value

def add_cover_frames(frame_info, frame_number, count, song, song_file_path):
    print(f"add_cover_frames: {frame_number}, {count}, {song_file_path}")
    graphic_path = song.get_cover_graphic_path(song_file_path)
    print(f"GRAPHIC {graphic_path}")
    path = IMAGE_ROOT_PATH + format_number(frame_number) + ".png"

    for x in range(0, count):
        frame_info.append(FrameInfo(frame_number + x, None, None, None, graphic_path))


def create_image_sequence(frame_info):
    curr = frame_info[0]
    frame = curr
    num_frames = 0
    generated_frame_count = 0
    prev_title = None
    
    for frame in frame_info:
        if (frame.num == 0):
            continue
        if ((curr.prompt == frame.prompt) and (curr.text == frame.text) and (curr.title == frame.title)):
            num_frames = num_frames + 1
        else:
            num_frames = num_frames + 1
            generate2(curr.num, num_frames, curr.prompt, prev_title != curr.title, curr.text, curr.title, curr.graphic_path)
            prev_title = curr.title
            generated_frame_count = generated_frame_count + num_frames
            curr = frame
            num_frames = 0

    
    generate2(curr.num, num_frames, curr.prompt, curr.text != frame.text, curr.text, curr.title, curr.graphic_path)
    generated_frame_count = generated_frame_count + num_frames + 1
    
    print(f"create_image_sequence generated {generated_frame_count} frames vs {len(frame_info)}")



    

def generate_blank2(frame_number, count, text, title):
    print(f"generate_blank2: {frame_number}, {count}, {text}, {title}")

    if (GEN_IMAGES):
        orig_path = BLANK_IMAGE_PATH
        if (title != None):
            path = IMAGE_TEMP_DIR + "blank_w_text.png"
            create_image.create_image3(SIZE_VIDEO, text, title, FONTSIZE, path)
            orig_path = path

        # TODO: currently ignoring blank text frames, determine if this should be changed

        for x in range(0, count + 1):
            copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
            create_image.copy_file(orig_path, copy_path)


def generate2(frame_number, count, prompt, is_new_lyric, text, title, graphic_path):
    print(f"generate2: {frame_number}, {count}, {prompt}, {is_new_lyric}, {text}, {title}, {graphic_path}")
    
    if (not (graphic_path is None)):
        print(f"generate graphic frames")
        for x in range(0, count + 1):
            copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
            create_image.copy_file(graphic_path, copy_path)
        return

 #TODO DEL   if (prompt is None):
 #       prompt = title

    if (prompt is None):
        generate_blank2(frame_number, count, text, title)
        return
    
    path = IMAGE_ROOT_PATH + format_number(frame_number) + ".png"
    if (GEN_IMAGES):
        if (MODE_VIDEO == 'Image'):
            initial = create_image_sd.create_image(SIZE_VIDEO, prompt, is_new_lyric, text, title, FONTSIZE, path, IMAGE_TEMP_DIR)
        else:
            initial = create_image.create_image(SIZE_VIDEO, prompt, is_new_lyric, text, title, FONTSIZE, path, IMAGE_TEMP_DIR);

        for x in range(1, count):
            copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
            create_image.copy_file(initial, copy_path)
        

def init():
    create_image.create_blank(SIZE_VIDEO, BLANK_IMAGE_PATH)


def get_audio_file_path(song_file_path, song):
    parent_directory = os.path.dirname(song_file_path)
    full_path = os.path.join(parent_directory, song.audio)

    return full_path


init()


# to start, print a list of create image calls to make

song = Song.create_from_file(song_file_path)
audio_path = get_audio_file_path(song_file_path, song)

current_frame = 0
current_lyric = None
current_prompt = None
frame_info = []
total_frames = timestamp_to_frames(song.length)
print(f"total_frames: {total_frames}")
print(len(frame_info))

cover_frame_count = 20 # FPS * 1
add_cover_frames(frame_info, current_frame, cover_frame_count, song, song_file_path)
current_frame = current_frame + cover_frame_count



for lyric_info in song.lyrics:

    print(f"loop: {current_frame} {current_lyric} {current_prompt}")
    next_ts = lyric_info['timestamp']
    next_frame = timestamp_to_frames(next_ts)
    next_lyric = lyric_info['lyric']
    next_prompt = lyric_info['prompt'] if 'prompt' in lyric_info else None 

    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = next_frame - current_frame

    if (num_frames < frames_to_next):
        # gen num_frames
        add_frame(frame_info, current_frame, num_frames, current_lyric, current_prompt)
        
        blank_frames = frames_to_next - num_frames
        add_blank_frame(frame_info, current_frame + num_frames, blank_frames)

    else:
        # gen frames_to_next
        add_frame(frame_info, current_frame, frames_to_next - 1, current_lyric, current_prompt)
        # blank frame to keep things visually clean
        add_blank_frame(frame_info, current_frame + frames_to_next - 1, 1)


    print(f"advancing to current frame by {frames_to_next}")
    current_frame = current_frame + frames_to_next
    current_lyric = next_lyric
    current_prompt = next_prompt


# last lyric
if not current_lyric is None:
    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = total_frames - current_frame

    if (num_frames < frames_to_next):
        # gen num_frames
        add_frame(frame_info, current_frame, num_frames, current_lyric, current_prompt)

        blank_frames = frames_to_next - num_frames
        add_blank_frame(frame_info, current_frame + num_frames, blank_frames)

    else:
        # gen frames_to_next
        add_frame(frame_info, current_frame, frames_to_next + 1, current_lyric, current_prompt)


# add titles
title_frames = len(song.titles) * 3 * FPS
curr_title_frame = cover_frame_count + (2 * FPS)

for title in song.titles:
    title_frame_count = 3 * FPS
    add_title(frame_info, title, curr_title_frame, title_frame_count)
    curr_title_frame = curr_title_frame + title_frame_count



# add credits
credit_frames = (len(song.credits) + 1) * 3 * FPS
curr_credit_frame = total_frames - credit_frames

for credit in song.credits:
    credit_frame_count = 3 * FPS
    add_credit(frame_info, credit, curr_credit_frame, credit_frame_count)
    curr_credit_frame = curr_credit_frame + credit_frame_count
    
i = 0
for f in frame_info:
    print(f"i: {i}, f: {f}")
    i = i + 1

# check frame_info integrity
i = 0
for frame in frame_info:
    if (frame.num != i):
        print(f"Frame {frame.num} is not right {frame.num} != {i}")
        exit(-1)
    i = i + 1



create_image_sequence(frame_info)

create_image.create_video(IMAGE_ROOT_PATH, FPS, audio_path, TARGET_VIDEO_PATH, total_frames)
