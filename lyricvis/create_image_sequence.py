from song import Song
import create_image
import create_image_sd
import os

SIZE_VGA = (640, 480)
FONTSIZE=20
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\"
BLANK_IMAGE_PATH = IMAGE_ROOT_PATH + "blank.png"
TARGET_VIDEO_PATH = "C:\\temp\\out.mp4"
GEN_IMAGES = True

FPS = 30
SECS_PER_WORD = 2
MAX_FRAMES = 100000

#song_file_path = 'assets/example_song.json'
song_file_path = 'assets/everlast_whatitslike.json'


class FrameInfo:
    def __init__(self, num, prompt, text):
        self.num = num
        self.prompt = prompt
        self.text = text

    def __str__(self):
        return f"FrameInfo(num='{self.num}', prompt='{self.prompt}', text='{self.text}')"


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
        frame_info.append(FrameInfo(frame_number + x, None, None))

def add_frame(frame_info, frame_number, count, lyric):
    print(f"add_frame: {frame_number}, {count}, {lyric}")
    if (lyric is None):
        add_blank_frame(frame_info, frame_number, count)
        return

    for x in range(0, count):
        frame_info.append(FrameInfo(frame_number + x, lyric, None))

def add_credit(frame_info, credit, frame_number, count):
    print(f"add_credit: {frame_number}, {count}, {credit}")
    for x in range(0, count):
        idx = frame_number + x
        frame = frame_info[frame_number + x]
        for key, value in credit.items():
            frame.text = key + ": " + value


def create_image_sequence(frame_info):
    curr = frame_info[0]
    frame = curr
    num_frames = 0
    generated_frame_count = 0
    prev_prompt = None
    
    for frame in frame_info:
        if (frame.num == 0):
            continue
        if ((curr.prompt == frame.prompt) and (curr.text == frame.text)):
            num_frames = num_frames + 1
        else:
            num_frames = num_frames + 1
            generate2(curr.num, num_frames, curr.prompt, prev_prompt != curr.prompt, curr.text)
            prev_prompt = curr.prompt
            generated_frame_count = generated_frame_count + num_frames
            curr = frame
            num_frames = 0

    
    generate2(curr.num, num_frames, curr.prompt, curr.prompt != frame.prompt, curr.text)
    generated_frame_count = generated_frame_count + num_frames
    
    print(f"create_image_sequence generated {generated_frame_count+1} frames vs {len(frame_info)}")



    

def generate_blank2(frame_number, count):
    print(f"generate_blank2: {frame_number}, {count}")

    if (GEN_IMAGES):
        for x in range(0, count + 1):
            copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
            create_image.copy_file(BLANK_IMAGE_PATH, copy_path)

def generate2(frame_number, count, lyric, is_new_lyric, text):
    print(f"generate2: {frame_number}, {count}, {lyric}, {is_new_lyric}, {text}")
    if (lyric is None):
        generate_blank2(frame_number, count)
        return
    
    path = IMAGE_ROOT_PATH + format_number(frame_number) + ".png"
    if (GEN_IMAGES):
        initial = create_image_sd.create_image(SIZE_VGA, lyric, is_new_lyric, text, FONTSIZE, path)

        for x in range(1, count):
            copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
            create_image.copy_file(initial, copy_path)
        

def init():
    create_image.create_blank(SIZE_VGA, BLANK_IMAGE_PATH)


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

total_frames = timestamp_to_frames(song.length)
print(f"total_frames: {total_frames}")

frame_info = []
print(len(frame_info))

for lyric_info in song.lyrics:

    print(f"loop: {current_frame} {current_lyric}")
    next_ts = lyric_info['timestamp']
    next_frame = timestamp_to_frames(next_ts)
    next_lyric = lyric_info['lyric']

    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = next_frame - current_frame

    if (num_frames < frames_to_next):
        # gen num_frames
        add_frame(frame_info, current_frame, num_frames, current_lyric)
        
        blank_frames = frames_to_next - num_frames
        add_blank_frame(frame_info, current_frame + num_frames, blank_frames)

    else:
        # gen frames_to_next
        add_frame(frame_info, current_frame, frames_to_next - 1, current_lyric)
        # blank frame to keep things visually clean
        add_blank_frame(frame_info, current_frame + frames_to_next - 1, 1)


    print(f"advancing to current frame by {frames_to_next}")
    current_frame = current_frame + frames_to_next
    current_lyric = next_lyric


# last lyric
if not current_lyric is None:
    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = total_frames - current_frame

    if (num_frames < frames_to_next):
        # gen num_frames
        add_frame(frame_info, current_frame, num_frames, current_lyric)

        blank_frames = frames_to_next - num_frames
        add_blank_frame(frame_info, current_frame + num_frames, blank_frames)

    else:
        # gen frames_to_next
        add_frame(frame_info, current_frame, frames_to_next, current_lyric)


# add credits
credit_frames = len(song.credits) * 3 * FPS
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
        print(f"Frame {frame.num} is not right")
        exit(-1)
    i = i + 1



create_image_sequence(frame_info)

#create_image.create_video(IMAGE_ROOT_PATH, FPS, audio_path, TARGET_VIDEO_PATH)
