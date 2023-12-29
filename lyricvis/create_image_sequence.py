from song import Song
import create_image
import os

SIZE_VGA = (640, 480)
FONTSIZE=20
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\"
BLANK_IMAGE_PATH = IMAGE_ROOT_PATH + "blank.png"
TARGET_VIDEO_PATH = "C:\\temp\\out.mp4"

FPS = 30
SECS_PER_WORD = 2
MAX_FRAMES = 100000

#song_file_path = 'assets/example_song.json'
song_file_path = 'assets/everlast_whatitslike.json'


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

def generate_blank(frame_number, count):
    print(f"generate_blank: {frame_number}, {count}")

    for x in range(0, count + 1):
        copy_path = IMAGE_ROOT_PATH + format_number(frame_number + x) + ".png"
        create_image.copy_file(BLANK_IMAGE_PATH, copy_path)

def generate(frame_number, count, lyric):
    print(f"generate: {frame_number}, {count}, {lyric}")
    if (lyric is None):
        generate_blank(frame_number, count)
        return
    
    path = IMAGE_ROOT_PATH + format_number(frame_number) + ".png"
    initial = create_image.create_image(SIZE_VGA, lyric, FONTSIZE, path)

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

for lyric_info in song.lyrics:

    print(f"loop: {current_frame} {current_lyric}")
    next_ts = lyric_info['timestamp']
    next_frame = timestamp_to_frames(next_ts)
    next_lyric = lyric_info['lyric']

    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = next_frame - current_frame - 1

    if (num_frames < frames_to_next):
        # gen num_frames
        generate(current_frame, num_frames, current_lyric)
        
        blank_frames = frames_to_next - num_frames
        generate_blank(current_frame + num_frames, blank_frames)

    else:
        # gen frames_to_next
        generate(current_frame, frames_to_next - 1, current_lyric)
        # blank frame to keep things visually clean
        generate_blank(current_frame + frames_to_next - 1, 1)


    print(f"advancing to current frame by {frames_to_next} + 1")
    current_frame = current_frame + frames_to_next + 1
    current_lyric = next_lyric


# last lyric
if not current_lyric is None:
    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = total_frames - current_frame - 1

    if (num_frames < frames_to_next):
        # gen num_frames
        generate(current_frame, num_frames, current_lyric)

        blank_frames = frames_to_next - num_frames
        generate_blank(current_frame + num_frames, blank_frames)
        pass
    else:
        # gen frames_to_next
        generate(current_frame, frames_to_next, current_lyric)


create_image.create_video(IMAGE_ROOT_PATH, FPS, audio_path, TARGET_VIDEO_PATH)
