#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
import sys
from sqlalchemy import func
from sqlalchemy import *


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#Import models file
from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.

  # query to get list of location
  locations = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  
  data = []
  for row in locations:
    # query to get list of Venue by city and state
    list_venues = (Venue.query.filter(and_(Venue.city==row[0], Venue.state==row[1])).all())

    # loop list for venues 
    i = 0
    venues = []
    while i < len(list_venues):
      venues.append({
        "id": list_venues[i].id,
        "name": list_venues[i].name,
        #num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all())
      })
      i = i + 1
  
    #Add city state and venue in data
    data.append(
      {
        "city": row[0],
        "state": row[1],
        "venues": venues
      }
    )
  
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term') 

  # query to filter venue by search_term
  search_results = Venue.query.filter(Venue.name.contains(search_term)).all()
 

  #add search result in resutls data
  results = []
  for search_result in search_results:
    results.append({
      "id": search_result.id,
      "name": search_result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == search_result.id).filter(Show.start_time > datetime.now()).all()),
    })



  response={
    "count": len(search_results),
    "data": results
  }

 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  all_venue_data = Venue.query.all()

  # query get list of upcoming show
  upcoming_show_list = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in upcoming_show_list:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  # query get list of past show
  past_show_list = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in past_show_list:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })


  # loop all_venue_data to insert in list_venue array
  list_venue = []
  for venue in all_venue_data:    
    list_venue.append(
      {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows":past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
      }
    )

  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]

  #filter list_venue by venue_id 
  try:
    data = list(filter(lambda d: d['id'] == venue_id, list_venue))[0]
  except:
    data = 'null'

#return error 404 template if data is null
  if data == 'null':
    return render_template('errors/404.html')
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm(request.form)

  # Controls if form is validate
  if form.validate():
    try:
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      address = request.form['address']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      facebook_link = request.form['facebook_link']
      image_link = request.form['image_link']
      website_link = request.form['website_link']

      #verifier if seeking_talent is in request.form
      if 'seeking_talent' in request.form:
        seeking_talent = True
      else:
        seeking_talent = False

      seeking_description = request.form['seeking_description']

      #create venue with Venue model
      venue = Venue(
        name = name,
        city = city, 
        state = state, 
        address = address,
        phone = phone,
        genres = genres,
        seeking_talent = seeking_talent,
        seeking_description = seeking_description,
        website_link = website_link,
        image_link = image_link,
        facebook_link = facebook_link)


      db.session.add(venue)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    # if form is not validate return venue form
    return render_template('forms/new_venue.html', form=form)


  
 # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  if error:
      # on error for db insert, flash error
     flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using

  error = False
  try:
    # query fot get venue by id and delete it
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # on error for venue delete, flash error
    flash(f'An error occured. Venue ' +venue_id+ ' couls not be deleted.')
  else:
    # on error for db delete, flash success
    flash(f'Venue '+ venue_id + ' was successfully deleted.')

  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  #get all artist
  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []

  #loop for search result and add in data array 
  #get len for upcoming show for artist search
  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id==result.id).filter(Show.start_time>datetime.now()).all())
    })

  #add data in reponse for render response on front
  response={
    "count":len(search_result),
    "data": data
  }


  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  # get all artist list
  artist_list = Artist.query.all()

  # join show and venue and filter by artist id to get past show list when start date are less than date now
  past_show_list = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows =[]

  # loop past show list for get past shows for artist
  for show in past_show_list:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  # join show and venue and filter by artist id to get past show list when start date are more than date now
  upcoming_show_list = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in upcoming_show_list:
    upcoming_shows.append({
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "venue_image_link": show.venue.image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  #loop artist list and add in artist array
  artists = []
  for artist in artist_list:
    artists.append({
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows":past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    })

  # filter artist list by id artist 
  try:
    data = list(filter(lambda d: d['id'] == artist_id, artists))[0]
  except:
    data = 'null'
  
  # render error 404 template if data is null
  if data == 'null':
    return render_template('errors/404.html')
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  # TODO: populate form with fields from artist with ID <artist_id>
  # get artist by artist id
  artist = Artist.query.get(artist_id)

  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description 

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False

  # get artist by id
  artist = Artist.query.get(artist_id)

  form = ArtistForm(request.form)

  # verifier artist form if is validate
  if form.validate():
    try:
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.image_link = request.form['image_link']
      artist.facebook_link = request.form['facebook_link']
      artist.website_link = request.form['website_link']

      if 'seeking_venue' in request.form:
        artist.seeking_venue = True
      else:
        artist.seeking_venue = False
      
      artist.seeking_description = request.form['seeking_description']

      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    # return edit artist form if form is not validate
    return render_template('forms/edit_artist.html', form=form, artist=artist) 
  
  if error:
    # flash error message for artist edit, flash error
    flash('An error occured. Artist' + request.form['name'] + ' could not be changed.')
  else:
    # flash success or message for artist edit, flash success
    flash('Artist '+ request.form['name'] + ' was successfully update!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
 
  #get venue by venue id
  venue = Venue.query.get(venue_id)

  # verifier id venue exist
  # TODO: populate form with values from venue with ID <venue_id>
  if venue:
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website_link
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update
  error = False
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)

  # verifier if form is validate 
  if form.validate():
    try:
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.website_link = request.form['website_link']

      # condition if seeking_talent is in request form
      if 'seeking_talent' in request.form:
        venue.seeking_talent = True
      else:
        venue.seeking_talent = False
      
      venue.seeking_description = request.form['seeking_description']

      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    return render_template('forms/edit_venue.html', form=form, venue=venue) 
  
  if error:
    # flash error message for form
    flash(f'An error occurred. Venue '+  request.form['name'] +' could not be changed.')
  else:
    # venue record with ID <venue_id> using the new attributes
    # flash  success message form 
    flash(f'Venue '+  request.form['name'] +'  was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error = False
  form = ArtistForm(request.form)

  if form.validate():
    try:
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      facebook_link = request.form['facebook_link']
      image_link = request.form['image_link']
      website_link = request.form['website_link']

      #verification si le dans la request il y a le
      if 'seeking_venue' in request.form:
        seeking_venue = True
      else:
        seeking_venue = False

      seeking_description = request.form['seeking_description']

      artist = Artist(
        name = name,
        city = city, 
        state = state, 
        phone = phone,
        genres = genres,
        seeking_venue = seeking_venue,
        seeking_description = seeking_description,
        website_link = website_link,
        image_link = image_link,
        facebook_link = facebook_link)

      print(artist)

      db.session.add(artist)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()
  else:
    return render_template('forms/new_artist.html', form=form)
  

 # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('artists'))
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  # query to get all show list 
  show_list = db.session.query(Show).join(Artist).join(Venue).all()


  data = []
  for show in show_list:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    artist_id = request.form['artist_id'] 
    venue_id = request.form['venue_id']
    start_time = request.form['start_time'] 

    show = Show(
      artist_id = artist_id,
      venue_id = venue_id,
      start_time = start_time
    )

    db.session.add(show)
    db.session.commit()

    print(request.form)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # on error db insert, flash error
    flash('An error occurred. Show could not be listed.')
    return redirect(url_for('shows'))
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    return render_template('pages/home.html')


  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''