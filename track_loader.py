#imports
import librosa
import pandas as pd
import numpy as np
from track import Track
from pathlib import Path

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

        print(track)

# df["genre_id"] # get column
# df.iloc[11] # get row
# df.iloc[11]["title"] # get cell