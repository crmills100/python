import json
import os

class Song:

    def __init__(self, title, artist, length, audio, cover_graphic, lyrics, titles=None, credits=None):
        self.title = title
        self.artist = artist
        self.length = length
        self.audio = audio
        self.cover_graphic = cover_graphic
        self.lyrics = lyrics
        self.titles = titles or []
        self.credits = credits or []

    def add_credit(self, role, name):
        self.credits.append({role: name})


    def display_info(self):
        print(f"Song Title: {self.title}")
        print(f"Artist: {self.artist}")
        print(f"Length: {self.length}")
        print(f"Audio: {self.audio}")
        print(f"Cover Graphic: {self.cover_graphic}")
        print("Lyrics:")
        for lyric_info in self.lyrics:
            print(f"Timestamp: {lyric_info['timestamp']} - Lyric: {lyric_info['lyric']}")

    def display_credits(self):
        if self.credits:
            print("Credits:")
            for credit in self.credits:
                for role, name in credit.items():
                    print(f"{role}: {name}")
        else:
            print("No credits available for this song.")



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
        cover_graphic = data['cover_graphic']
        lyrics = data['lyrics']
        titles = data['titles']
        song = Song(song_title, artist, length, audio, cover_graphic, lyrics, titles)

        # Parse and add credits from JSON data
        credits = data['credits']
        if credits:
            for credit in credits:
                for role, name in credit.items():
                    song.add_credit(role, name)


        return song
    
    def get_cover_graphic_path(self, path):
        graphic_directory = os.path.dirname(path)

        print(f"self.cover_graphic: {self.cover_graphic}")
        print(f"graphic_directory: {graphic_directory}")
    
        cover_graphic_path = os.path.join(graphic_directory, self.cover_graphic)
        print(f"cover_graphic_path: {cover_graphic_path}")
        
        return cover_graphic_path