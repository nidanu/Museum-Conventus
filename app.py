#!/usr/bin/env python 
"""
App file for Museum Conventus website. It uses a database to store API information from three museums.
Each museum has a slighly different structure to their JSON response, so three functions run at the same time to collect the information and store it.
The database is cleared for every new search.

Usage: 
--> export DATABASE_URL=“postgresql://localhost/Project”
--> python3 -m flask --debug run

By: Nidanu O'Shea
"""

# Imports
import os
import asyncio
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from helpers import *
from sqlalchemy import func

app = Flask(__name__)
app.debug = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///museumconventus.db'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Initialize SQLAlchemy with Flask
db.init_app(app)
Session(app)

@app.route("/")
def index():
    """Route to home page."""

    # Clear database and session
    session.clear()
    db.drop_all()
    db.create_all()
    
    return redirect("/search")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Obtains keyword and runs functions to collect data."""

    # Clear database and session
    session.clear()
    db.drop_all()
    db.create_all()

    if request.method == "POST":

        # Save the user's search term
        keyword = request.form.get("keyword")
        session["keyword"] = keyword

        # Obtain API data: see helpers.py
        asyncio.run(get_data(keyword))

        return redirect("/results")
    else:
        return render_template("search.html")

@app.route("/results", methods=["GET"])
def results():
    """Queries database for information needed to configure results page."""

    header = f"Search results for '{session['keyword']}'"

    # No selected checkboxes
    selectedTypes = []

    # Lists all possible mediums listed for the keyword 
    mediums = db.session.execute("SELECT medium FROM Artwork GROUP BY medium ORDER BY medium ASC").fetchall()
    mediums = [medium[0] for medium in mediums if medium[0] != ''] 

    # Number of results per page
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Counts number of results
    total_results = Artwork.query.count()

    if total_results == 0:
        header = f"No results for '{session['keyword']}'"

    # Results ordered by their ID
    works = Artwork.query.order_by(Artwork.title, Artwork.artist).paginate(page=page, per_page=per_page)
    return render_template("results.html", header=header, works=works, mediums=mediums, total_results=total_results, selectedTypes=selectedTypes)

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    """Applies filters to search results, using AJAX imprted information."""

    # Import information from JS in results.html 
    data = request.form

    # Checked filter boxes
    selectedTypes = data.getlist('selectedTypes[]')

    # Date range
    fromDate = data.get('fromDate')
    toDate = data.get('toDate')

    # Number of results per page
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Possible mediums to filter over
    mediums = db.session.execute("SELECT medium FROM Artwork GROUP BY medium ORDER BY medium ASC").fetchall()
    mediums = [medium[0] for medium in mediums if medium[0] != ''] 
    header = f"Search results for '{session['keyword']}'"

    # If any checkboxes are checked
    if len(selectedTypes) > 0:

        # Checks if date restrictions have been added
        if fromDate and toDate:
            works = Artwork.query.filter((Artwork.medium.in_(selectedTypes)), (Artwork.date >= fromDate),(Artwork.date <= toDate)).paginate(page=page, per_page=per_page)
            total_results = Artwork.query.filter((Artwork.medium.in_(selectedTypes)), (Artwork.date >= fromDate),(Artwork.date <= toDate)).count()
        elif fromDate:
            works = Artwork.query.filter((Artwork.medium.in_(selectedTypes)), (Artwork.date >= fromDate)).paginate(page=page, per_page=per_page)
            total_results = Artwork.query.filter((Artwork.medium.in_(selectedTypes)), (Artwork.date >= fromDate)).count()
        elif toDate:
            works = Artwork.query.filter((Artwork.medium.in_(selectedTypes)),(Artwork.date <= toDate)).paginate(page=page, per_page=per_page)
            total_results = Artwork.query.filter_by((Artwork.medium.in_ in selectedTypes),(Artwork.date <= toDate)).count()
        else:
            works = Artwork.query.filter((Artwork.medium.in_(selectedTypes))).paginate(page=page, per_page=per_page)
            total_results = Artwork.query.filter((Artwork.medium.in_(selectedTypes)))
    
    # If no filters selected
    else:
        total_results = Artwork.query.count()
        selectedTypes = []
        works = Artwork.query.order_by(Artwork.id).paginate(page=page, per_page=per_page)

    return render_template("results.html", header=header, works=works, mediums=mediums, total_results=total_results, selectedTypes=selectedTypes)
    
@app.route("/museums", methods=["POST", "GET"])
def museums():
    """Route to page indicating which museum collections are used on the site."""
    museum_list = [("Victoria and Albert Museum", "https://www.vam.ac.uk/"),("Rijksmuseum", "https://www.rijksmuseum.nl/en"),("Metropolitan Museum of Art","https://www.metmuseum.org/")]
    if request.method == "GET":
        museum_list = sorted(museum_list)
        return render_template("museums.html", museum_list=museum_list)

@app.route("/about", methods=["GET", "POST"])
def about():
    """Route to about page."""

    return render_template("about.html")