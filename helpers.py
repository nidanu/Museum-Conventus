"""
Extra functions and models to support app.py.

By: Nidanu O'Shea
"""

# Imports
import aiohttp
import requests
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database table format
class Artwork(db.Model):
    __tablename__ = 'artwork'
    hash = db.Column(db.Integer, primary_key=True, nullable=False)
    id = db.Column(db.String)
    title = db.Column(db.String)
    artist = db.Column(db.String)
    medium = db.Column(db.String)
    date = db.Column(db.String)
    url = db.Column(db.String)
    image_url = db.Column(db.String)
    museum = db.Column(db.String)
    museum_url = db.Column(db.String)

async def fetch_data(session, url):
    """Function to speed up API data collection."""

    async with session.get(url) as response:
        return await response.json()
    
async def fetch_va_data(keyword):
    """Obtain information from VICTORIA & ALBERT MUSEUM API. Initial call returns info over all results.
    The V&A API only permits a maximum of 100 results per call."""

    async with aiohttp.ClientSession() as session:
        
        # JSON response
        va_response = requests.get("https://api.vam.ac.uk/v2/objects/search?q=%s&page_size=100" % keyword)
        va_jsondata = va_response.json()

        if 'records' in va_jsondata.keys():
            va_json = va_jsondata["records"]
        for i in range(len(va_json)):
            if va_json[i]["systemNumber"] is not None:
                id = va_json[i]["systemNumber"]
                title = va_json[i]["_primaryTitle"]
                if 'name' in va_json[i]["_primaryMaker"].keys():
                    artist = va_json[i]["_primaryMaker"]["name"]
                url = "https://collections.vam.ac.uk/item/%s" % (id)
                medium = va_json[i]["objectType"]
                date = va_json[i]["_primaryDate"]
                if va_json[i]["_primaryImageId"] is not None:
                    image_url = va_json[i]["_images"]["_primary_thumbnail"]
                else:
                    image_url = "static/no_image.jpg"
                museum = "Victoria and Albert Museum"
                museum_url = "https://www.vam.ac.uk/"
               
               # Add artwork to database
                artwork = Artwork(hash=hash(id), id=id, title=title, artist=artist, medium=medium, date=date, url=url, image_url=image_url, museum=museum, museum_url=museum_url)
                db.session.add(artwork)
                db.session.commit()

async def fetch_met_data(keyword):
    """Obtain information from METROPOLITAN MUSEUM OF ART API. First call returns list of all object IDs.
    Second call returns information of each object using their ID. The API is limited to 80 requests per second,
    so the number of results is capped at 100 to speed up the website."""

    async with aiohttp.ClientSession() as session:

        # JSON response: First call
        met_response = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/search?q=%s" % keyword)
        met_jsondata = met_response.json()
        met_IDs = []
        if 'objectIDs' in met_jsondata.keys():
            met_IDs = list(met_jsondata["objectIDs"])

        # If results found in the MET collection
        if len(met_IDs) > 0:
            for i in range(100):

                # Second call
                metID_response = requests.get("https://collectionapi.metmuseum.org/public/collection/v1/objects/%s" % met_IDs[i]) 
                metID_jsondata = metID_response.json()
                if 'objectID' in metID_jsondata.keys():
                    id = metID_jsondata["objectID"]
                    title = metID_jsondata["title"]
                    artist = metID_jsondata["artistDisplayName"]
                    url = metID_jsondata["objectURL"]
                    date = metID_jsondata["objectDate"]
                    medium = metID_jsondata["objectName"]
                    if metID_jsondata["isPublicDomain"] is True:
                        image_url = metID_jsondata["primaryImage"]
                    else:
                        image_url = "static/no_image.jpg"
                    museum = "Metropolitan Museum of Art"
                    museum_url= "https://www.metmuseum.org/"

                    # Add artwork to database
                    artwork = Artwork(hash=hash(id), id=id, title=title, artist=artist, medium=medium, date=date, url=url, image_url=image_url, museum=museum, museum_url=museum_url)
                    db.session.add(artwork)
                    db.session.commit()

async def fetch_rijks_data(keyword):
    """Obtain information from RIJKSMUSEUM API. Initial call returns basic info over all results.
    Second call returns item specific information, i.e., the item ID is used to obtain details."""

    async with aiohttp.ClientSession() as session:

        # JSON response: First call
        rijks_response = requests.get("https://www.rijksmuseum.nl/api/en/collection?key=D82d0Rur&q=%s" % keyword)
        rijks_jsondata = rijks_response.json()
        if 'artObjects' in rijks_jsondata.keys():
            rijks_json = rijks_jsondata["artObjects"]
        for i in range(len(rijks_json)):
            id = rijks_json[i]["objectNumber"]
            title = rijks_json[i]["title"]
            artist = rijks_json[i]["principalOrFirstMaker"]
            url = rijks_json[i]["links"]["web"]
            if rijks_json[i]["webImage"] is not None:
                image_url = rijks_json[i]["webImage"]["url"]
            else:
                image_url = "static/no_image.jpg"
            museum = "Rijksmuseum"
            museum_url= "https://www.rijksmuseum.nl/en"

            # Second call
            id_response = requests.get("https://www.rijksmuseum.nl/api/en/collection/%s?key=D82d0Rur" % id)
            id_jsondata = id_response.json()
            medium = ""
            date = ""
            if 'artObjects' in id_jsondata.keys():
                medium  = id_jsondata["artObjects"]["objectTypes"][0]
                date = id_jsondata["artObjects"]["dating"]["presentingDate"]
            
            # Add artwork to database
            artwork = Artwork(hash=hash(id), id=id, title=title, artist=artist, medium=medium, date=date, url=url, image_url=image_url, museum=museum, museum_url=museum_url)
            db.session.add(artwork)
            db.session.commit()

async def get_data(keyword):
    """Fetch data from museum APIs."""

    await fetch_va_data(keyword)
    await fetch_met_data(keyword)
    await fetch_rijks_data(keyword)