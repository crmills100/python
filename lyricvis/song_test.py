import unittest
from song import Song

class TestSongClass(unittest.TestCase):
    def setUp(self):
        pass

    def test_song_object_creation(self):
        path = 'assets/example_song.json'
        song = Song.create_from_file(path)
        self.assertEqual(song.title, "Example Song")
        self.assertEqual(song.artist, "Example Artist")
        self.assertEqual(song.audio, "example.mp3")
        self.assertEqual(len(song.lyrics), 4)

        song.display_info()
        song.display_credits()
        song.get_cover_graphic_path(path)

if __name__ == '__main__':
    unittest.main()


