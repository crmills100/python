import unittest
import create_image_sd

SIZE_VGA = (640, 480)
FONTSIZE=30
IMAGE_ROOT_PATH = "C:\\temp\\lyric_vis\\temp\\"


class CreateImageTest(unittest.TestCase):
    def setUp(self):
        pass



    def test_create_image_sd(self):
        create_image_sd.create_image(SIZE_VGA, "'Cause then you really might know what it's like to sing the blues", True, "Produced By: Christopher Mills", None, FONTSIZE, IMAGE_ROOT_PATH + "A_01.png", IMAGE_ROOT_PATH)
        

if __name__ == '__main__':
    unittest.main()

