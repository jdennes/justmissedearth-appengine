
from google.appengine.ext import db

class CloseApproach(db.Model):
    object_name = db.StringProperty(required=True)
    approach_date = db.DateTimeProperty(required=True)
    minimum_distance_away = db.IntegerProperty(required=True)
    relative_velocity = db.FloatProperty(required=True)
    estimated_diameter = db.IntegerProperty(required=True)
    date_added = db.DateTimeProperty(auto_now_add=True)
    date_tweeted = db.DateTimeProperty(required=False)
