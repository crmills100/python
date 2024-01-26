import unittest
from song import Song

class TestSongClass(unittest.TestCase):
    def setUp(self):
        pass

    def test_song_object_creation(self):
        song = Song.create_from_file('assets/example_song.json')
        self.assertEqual(song.title, "Example Song")
        self.assertEqual(song.artist, "Example Artist")
        self.assertEqual(song.audio, "example.mp3")
        self.assertEqual(len(song.lyrics), 4)

        song.display_info()
        song.display_credits()

if __name__ == '__main__':
    unittest.main()


