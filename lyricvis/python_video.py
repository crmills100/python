import moviepy.editor as mpy
from moviepy.video.tools.segmenting import findObjects

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\\opt\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"})

WHITE = (255, 255, 255)
SCREEN_SIZE = (640, 480)
VERTICAL_SPACE = 30
HORIZONTAL_SPACE = 40

SB_LOGO_PATH = "./assets/StackBuildersLogo.jpg"

sb_logo = mpy.ImageClip(SB_LOGO_PATH).\
    set_position(('center', 0)).\
    resize(width=200)

txt_clip = mpy.TextClip(
    "Let's build together",
    font = "Charter-bold",
    color = "RoyalBlue4",
    kerning = 4,
    fontsize = 30,
).\
set_position(("center", sb_logo.size[1] + VERTICAL_SPACE))



STARS_PATH = "./assets/stars-5.png"

stars_clip = mpy.CompositeVideoClip(
    [mpy.ImageClip(STARS_PATH).set_position("center")], size=SCREEN_SIZE
)
stars = findObjects(stars_clip)
stars2 = []
for i, star in enumerate(stars): 
    stars2.append(star)
    stars2.append(star)
    
    
CLOCKWISE_ANGLE = -90

def rotate(stars):
    return [
        star.rotate(lambda t: t * CLOCKWISE_ANGLE, expand = False)
        .fx(mpy.vfx.mask_color)
        .set_position(((i+1) * HORIZONTAL_SPACE, sb_logo.size[1] + txt_clip.size[1] + VERTICAL_SPACE * 2))
        for i, star in enumerate(stars)
    ]

phrases = []
phrases.append("B")
phrases.append("Bu")
phrases.append("Bul")
phrases.append("Buli")
phrases.append("Bulid")
phrases.append("Bulid ")
phrases.append("Bulid T")
phrases.append("Bulid Th")
phrases.append("Bulid Thi")
phrases.append("Bulid This")



def myText():
    return [ txt_clip    ]

final_clip = (
    mpy.CompositeVideoClip([sb_logo] + myText(), size=SCREEN_SIZE)
    .on_color(color=WHITE, col_opacity=1)
    .set_duration(10)
)

final_clip.write_videofile("video_with_python.mp4", fps=10)



