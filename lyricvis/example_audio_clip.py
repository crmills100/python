from moviepy.editor import *
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})


audio_path = "assets/everlast_whatitslike.mp3"
output_path = "C:\\temp\\clipout.mp3"

rmbintro = AudioFileClip("assets/r3hab_rockmybody.mp3").subclip(2, 19.4)


rmbmain = AudioFileClip("assets/r3hab_rockmybody.mp3").subclip(50.1, 58)

laylowhook = AudioFileClip("assets/tiesto_laylow.mp3").subclip(55.5, 71)

fadedbaby = AudioFileClip("assets/zhu_faded.mp3").subclip(89.4, 106.5)


silent_array = np.random.uniform(0, 0, (44100*1, 2)) # np.zeros(int(1 * 44100))

silent_clip = AudioArrayClip(silent_array, fps=44100)

start_time = 60
duration = 10
clip2 = AudioFileClip(audio_path).subclip(start_time, start_time + duration)

concatenated_audioclips = concatenate_audioclips([rmbintro, laylowhook, fadedbaby, silent_clip])




concatenated_audioclips.write_audiofile(output_path, codec="mp3")



