# imports
import json
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

        # Track features
        self.mfcc_mean = None
        self.mfcc_std = None
        self.centroid_mean = None
        self.centroid_std = None
        self.zcr_mean = None
        self.zcr_std = None
        self.rms_mean = None
        self.rms_std = None

    def __str__(self):
        return f"id: {self.track_id}\nfilepath: {self.filepath}\nsample rate: {self.sample_rate}\ntitle: {self.title}\nartist: {self.artist}\nalbum: {self.album}\ngenres: {self.genres}"

    def print_stats(self):
        print("mfcc mean: ", self.mfcc_mean)
        print("mfcc std: ", self.mfcc_std)
        print("centroid mean: ", self.centroid_mean)
        print("centroid std: ", self.centroid_std)
        print("zero crossings mean: ", self.zcr_mean)
        print("zero crossings std: ", self.zcr_std)
        print("rms mean: ", self.rms_mean)
        print("rms std: ", self.rms_std)

    def save(self):
        data = {
            "track id" : self.track_id,
            "filepath" : self.filepath,
            "sample rate" : self.sample_rate,
            "title" : self.title,
            "artist" : self.artist,
            "album" : self.album,
            "genres" : self.genres
        }

        with open("tracks.json", "w") as file:
            json.dump(data, file)