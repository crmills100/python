import unittest
import create_image
import create_image_sd

SIZE_VGA = (640, 480)
FONTSIZE=30
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\temp\\"


class CreateImageTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_create_image(self):
        create_image.create_image(SIZE_VGA, "This is a test!!", FONTSIZE, IMAGE_ROOT_PATH + "001.png")

    def test_create_blank(self):
        create_image.create_blank(SIZE_VGA, IMAGE_ROOT_PATH + "blank.png")

    def test_create_image_sd(self):
        create_image_sd.create_image(SIZE_VGA, "'Cause then you really might know what it's like to sing the blues", True, "Produced By: Christopher Mills", FONTSIZE, IMAGE_ROOT_PATH + "A_01.png", IMAGE_ROOT_PATH)
        
    def test_overlay_images(self):
        background_path = IMAGE_ROOT_PATH + "background.png"
        create_image.create_image(SIZE_VGA, "This is a test!!", FONTSIZE, background_path)

        overlay_path = IMAGE_ROOT_PATH + "overlay.png"
        create_image.create_transparent_image(SIZE_VGA, "More text", FONTSIZE, overlay_path)

        output_path = IMAGE_ROOT_PATH + "overlay_output.png"
        create_image.overlay_images(background_path, overlay_path, output_path)

if __name__ == '__main__':
    unittest.main()

