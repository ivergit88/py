import typing as tp
import sqlite3


class DataBaseHandler:
    def __init__(self, sqlite_database_name: str):
        """
        Initialize all the context for working with database here
        :param sqlite_database_name: path to the sqlite3 database file
        """
        self._conn = sqlite3.connect(sqlite_database_name)
        self._conn.row_factory = sqlite3.Row

    def get_most_expensive_track_names(self, number_of_tracks: int) -> tp.Sequence[tuple[str]]:
        """
        Return the sequence of track names sorted by UnitPrice descending.
        If the price is the same, sort by TrackId ascending.
        :param number_of_tracks: how many track names should be returned
        keywords: SELECT, ORDER BY, LIMIT
        :return:
        """
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT Name
            FROM tracks
            ORDER BY UnitPrice DESC, TrackId ASC
            LIMIT ?
        """, (number_of_tracks,))
        return [tuple(row) for row in cursor.fetchall()]

    def get_tracks_of_given_genres(self, genres: tp.Sequence[str], number_of_tracks: int) -> tp.Sequence[tuple[str]]:
        """
        Return the sequence of track names that have one of the given genres
        sort asending by track duration and limit by number_of_tracks
        :param number_of_tracks:
        :param genres:
        keywords: JOIN, WHERE, IN
        :return:
        """
        cursor = self._conn.cursor()
        placeholders = ','.join(['?'] * len(genres))
        query = f"""
            SELECT t.Name
            FROM tracks t
            JOIN genres g ON t.GenreId = g.GenreId
            WHERE g.Name IN ({placeholders})
            ORDER BY t.Milliseconds ASC
            LIMIT ?
        """
        cursor.execute(query, list(genres) + [number_of_tracks])
        return [tuple(row) for row in cursor.fetchall()]

    def get_tracks_that_belong_to_playlist_found_by_name(self, name_needle: str) -> tp.Sequence[tuple[str, str]]:
        """
        Return a sequence of track names and playlist names such that the track belongs to the playlist and
        the playlist's name contains `name_needle` (case sensitive).
        If the track belongs to more than one suitable playlist it
        should occur in the result for each playlist, but not just once
        :param name_needle:
        keywords: JOIN, WHERE, LIKE
        :return:
        """
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT t.Name, p.Name
            FROM playlists pl
            JOIN playlist_track pt ON pl.PlaylistId = pt.PlaylistId
            JOIN tracks t ON pt.TrackId = t.TrackId
            JOIN playlists p ON pl.PlaylistId = p.PlaylistId
            WHERE p.Name LIKE ?
            ORDER BY t.Name, p.Name
        """, (f'%{name_needle}%',))
        return [tuple(row) for row in cursor.fetchall()]

    def teardown(self) -> None:
        """
        Cleanup everything after working with database.
        Do anything that may be needed or leave blank
        :return:
        """
        self._conn.close()
