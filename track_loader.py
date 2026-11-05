#imports
import librosa
import pandas as pd
import numpy as np
from track import Track
from pathlib import Path

# get path to song
path = Path("fma_small/000/000002.mp3")

# create the track and load the audio
track = Track(path.stem, path)
track.audio, track.sample_rate = librosa.load(path)

# get metadata
df = pd.read_csv("fma_metadata/tracks.csv", low_memory=False)

row = df[df.iloc[:, 0] == str(int(path.stem))]
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

### Loop over all songs
# path2 = Path("fma_small")

# for file in path2.rglob("*"):
#     if file.is_file():
#         print(file.name)