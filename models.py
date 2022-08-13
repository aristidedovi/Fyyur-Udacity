from app import db

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()), default=[])
    seeking_talent = db.Column(db.Boolean(), default=False, server_default="false")
    seeking_description = db.Column(db.String())
    website_link = db.Column(db.String(120))
    show = db.relationship("Show", backref="venue", uselist=False)


    def __repr__(self):
      return f'<Venue Name:{self.name}  Genre:{self.genres}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean())
    seeking_description = db.Column(db.String())
    website_link = db.Column(db.String(120))
    show = db.relationship("Show", backref="artist", uselist=False)


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id =  db.Column(db.Integer, db.ForeignKey("artist.id"))
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
  start_time = db.Column(db.DateTime, nullable=False)