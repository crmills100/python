import create_image_sd

SIZE_VGA = (640, 480)
FONTSIZE=30
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\temp\\"

create_image_sd.create_image(
    SIZE_VGA, 
    "\"What It's Like\"\n Everlast\n Whitney Ford Sings the Blues", 
    True, 
    "A Generative AI Music Video", 
    FONTSIZE, 
    IMAGE_ROOT_PATH + "wil_title.png", 
    IMAGE_ROOT_PATH, 
    "#76B900")