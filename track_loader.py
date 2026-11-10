#imports
import librosa
import pandas as pd
import numpy as np
from track import Track
from pathlib import Path

# calculate mfcc's on a track and then get 20 means and 20 stds for that track
def get_mfcc(track):
    mfcc = librosa.feature.mfcc(y = track.audio, sr = track.sample_rate)

    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    track.mfcc_mean = mfcc_mean
    track.mfcc_std = mfcc_std

# calculate centroid and get the mean and std for that track
def get_spectral_centroid(track):
    centroid = librosa.feature.spectral_centroid(y = track.audio, sr = track.sample_rate)

    centroid_mean = np.mean(centroid, axis=1)
    centroid_std = np.std(centroid, axis=1)

    track.centroid_mean = centroid_mean
    track.centroid_std = centroid_std

# calculate zero crossing mean and std
def get_zero_crossings(track):
    zcr = librosa.feature.zero_crossing_rate(track.audio)

    zcr_mean = np.mean(zcr, axis=1)
    zcr_std = np.std(zcr, axis=1)

    track.zcr_mean = zcr_mean
    track.zcr_std = zcr_std

# calculate rms mean and std
def get_rms(track):
    rms = librosa.feature.rms(y=track.audio)

    rms_mean = np.mean(rms, axis=1)
    rms_std = np.std(rms, axis=1)

    track.rms_mean = rms_mean
    track.rms_std = rms_std

### Loop over all songs
path_og = Path("fma_small")
invalid_files = []
invalid_file_count = 0

for file in path_og.rglob("*.mp3"):
    if file.is_file():
        # get path to song
        #path = Path("fma_small/000/000002.mp3")
        path_name = str(file)

        # create the track and load the audio
        track = Track(file.stem, path_name)
        try:
            track.audio, track.sample_rate = librosa.load(file, sr=22050, mono=True)
        except:
            invalid_files.append(file.stem)
            invalid_file_count += 1

        # get metadata
        df = pd.read_csv("fma_metadata/tracks.csv", low_memory=False)

        row = df[df.iloc[:, 0] == str(int(file.stem))]
        title_column = "track.19"
        artist_column = "artist.12"
        album_column = "album.10"
        genres_column = "track.8"
        track.title = row[title_column].iloc[0]
        track.artist = row[artist_column].iloc[0]
        track.album = row[album_column].iloc[0]

        # get genres
        genre_titles = []
        genres = row[genres_column].iloc[0]
        genres_list = genres.strip("[]").split(",")
        genres_list = [int(x) for x in genres_list]
        df_genres = pd.read_csv("fma_metadata/genres.csv")
        # Add all genres listed to track object
        genre_column = "title"
        for genre in genres_list:
            genre_row = df_genres[df_genres.iloc[:, 0] == genre]
            genre_titles.append(genre_row[genre_column].iloc[0])
        track.genres = genre_titles

        # calculate feature stats
        get_mfcc(track)
        get_spectral_centroid(track)
        get_zero_crossings(track)
        get_rms(track)

        print(track)
        track.print_stats()

# df["genre_id"] # get column
# df.iloc[11] # get row
# df.iloc[11]["title"] # get cell