import json

class Song:

    def __init__(self, title, artist, lyrics):
        self.title = title
        self.artist = artist
        self.lyrics = lyrics

    def display_info(self):
        print(f"Song Title: {self.title}")
        print(f"Artist: {self.artist}")
        print("\nLyrics:")
        for lyric_info in self.lyrics:
            print(f"Timestamp: {lyric_info['timestamp']} - Lyric: {lyric_info['lyric']}")

   
    @staticmethod
    def create_from_file(path):
        # Read JSON file
        with open(path, 'r') as file:
            data = json.load(file)

        # Extract song information
        song_title = data['song_title']
        artist = data['artist']
        lyrics = data['lyrics']

        song = Song(song_title, artist, lyrics)

        return song
    
    
        