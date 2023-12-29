from song import Song


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
    # TODO

def generate(frame_number, count, lyric):
    print(f"generate: {frame_number}, {count}, {lyric}")
    # TODO



# to start, print a list of create image calls to make

FPS = 30
SECS_PER_WORD = 2

song = Song.create_from_file('assets/example_song.json')

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
        generate(current_frame, frames_to_next, current_lyric)


    print(f"advancing to current frame by {frames_to_next} + 1")
    current_frame = current_frame + frames_to_next + 1
    current_lyric = next_lyric


# last lyric
if not current_lyric is None:
    word_count = count_words(current_lyric)
    num_frames = word_count * SECS_PER_WORD * FPS

    frames_to_next = total_frames - current_frame

    if (num_frames < frames_to_next):
        # gen num_frames
        generate(current_frame, num_frames, current_lyric)

        blank_frames = frames_to_next - num_frames
        generate_blank(current_frame + num_frames, blank_frames)
        pass
    else:
        # gen frames_to_next
        generate(current_frame, frames_to_next, current_lyric)



