
from sre_constants import error
from ytmusicapi import YTMusic
import re
import random


class YT:

    def __init__(self):
        self.ytmusic = YTMusic()
        self.country = "US" # needed for top charts
    
    def generalQuery(self, query):
        """
        Responds to a general query
        """
        ret = self.ytmusic.search(query=query, filter="songs")[0]
        return [self.generalResp(ret)]
    
    def topChartsQuery(self, count):
        """
        Gets the top 10 trending songs in specified country
        """
        if count < 1 or count > 40:
            print("Invalid count given")
            exit()
        trending = self.ytmusic.get_charts(self.country)["trending"]["items"][:count]
        resps = [f"Top {count} trending songs:"]
        i = 1
        for song in trending:
            resps.append(self.topChartsResp(song, i))
            i += 1
        return resps
    
    def generalResp(self, songObj):
        """
        Formats the response of a general query
        """
        artists = songObj["artists"]
        album = songObj["album"]
        title = songObj["title"] # TODO: filter non song title parts in title vvvvv
        # title = re.sub(r" ?[\(\[]Official Video[\)\]]", "", re.sub(r" ?\[\(\[]feat. .+[\)\]] ?", "", song["title"]))
        linkid = songObj["videoId"]

        strArts = " and ".join([a["name"] for a in artists])
        resp = title + " by " + strArts + " from the album " + album["name"] + ". "
        resp = f"{title} by {strArts} from the album {album['name']}. "
        resp += "You can listen at www.youtube.com/watch?v=" + linkid
        return resp
    
    def topChartsResp(self, songObj, rank):
        """
        Formats the response for one top charts line
        """
        artists = songObj["artists"]
        title = self.cleanTitle(songObj["title"], artists)
        linkid = songObj["videoId"]
        
        strArts = " and ".join([a["name"] for a in artists])
        resp = f"   {rank}. {title} by {strArts} (www.youtube.com/watch?v={linkid})"
        return resp

    def cleanTitle(self, title, artists):
        """
        Youtube titles are often messy with excess information. This function
        returns just the actual title of the song.
        Ex:
            (Official Video) Katy Perry - Roar (Official Audio) feat. Someone by Katy Perry

            Returns: Roar
        """
        title = re.sub(r" ?[\(\[]Official .+[\)\]]", "", re.sub(r" ?\[\(\[]feat. .+[\)\]] ?", "", title))
        for artist in artists:
            artName = artist["name"]
            title = re.sub(artName + r" ?- ?", "", title)
        return title
        
    def randomSongQuery(self, query):
        """
        Given the name of an artist, find a random song by them
        """
        # TODO
        ret = self.ytmusic.search(query=query, filter="songs")
        song = ret[random.choice(range(len(ret)))]
        return [self.generalResp(song)]