import unittest
import create_image

SIZE_VGA = (640, 480)
FONTSIZE=30
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\temp\\"


class CreateImageTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_create_image(self):
        create_image.create_image(SIZE_VGA, "This is a test!!", FONTSIZE, IMAGE_ROOT_PATH + "001.png")

    def test_create_blank(self):
        create_image.create_blank(SIZE_VGA, IMAGE_ROOT_PATH + "blank_640x480.png")

    def test_overlay_images(self):
        background_path = IMAGE_ROOT_PATH + "background.png"
        create_image.create_image(SIZE_VGA, "This is a test!!", FONTSIZE, background_path)

        overlay_path = IMAGE_ROOT_PATH + "overlay.png"
        create_image.create_transparent_image(SIZE_VGA, "More text", FONTSIZE, overlay_path)

        output_path = IMAGE_ROOT_PATH + "overlay_output.png"
        create_image.overlay_images(background_path, overlay_path, output_path)

if __name__ == '__main__':
    unittest.main()

