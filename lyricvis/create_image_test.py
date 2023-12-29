import unittest
import create_image

SIZE_VGA = (640, 480)
FONTSIZE=30
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\"


class CreateImageTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_create_image(self):
        create_image.create_image(SIZE_VGA, "This is a test!!", FONTSIZE, IMAGE_ROOT_PATH + "001.png")

    def test_create_blank(self):
        create_image.create_blank(SIZE_VGA, IMAGE_ROOT_PATH + "blank.png")

if __name__ == '__main__':
    unittest.main()









