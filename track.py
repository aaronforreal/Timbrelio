# imports

class Track:
    def __init__(self, track_id, filepath):
        # General track info
        self.track_id = track_id
        self.filepath = filepath

        # Track audio info
        self.audio = None
        self.sample_rate = None

        # Track metadata (from tracks.csv)
        self.title = None
        self.artist = None
        self.album = None
        self.genres = None

    def __str__(self):
        return f"id: {self.track_id}\nfilepath: {self.filepath}\nsample rate: {self.sample_rate}\ntitle: {self.title}\nartist: {self.artist}\nalbum: {self.album}\ngenres: {self.genres}"
