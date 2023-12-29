import json

class Song:

    def __init__(self, title, artist, length, audio, lyrics):
        self.title = title
        self.artist = artist
        self.length = length
        self.audio = audio
        self.lyrics = lyrics

    def display_info(self):
        print(f"Song Title: {self.title}")
        print(f"Artist: {self.artist}")
        print(f"Length: {self.length}")
        print(f"Audio: {audio}")
        print("Lyrics:")
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
        length = data['length']
        audio = data['audio']
        lyrics = data['lyrics']

        song = Song(song_title, artist, length, audio, lyrics)

        return song
    
    
        