import sys, os
import traceback
import base64
import urllib, urllib2
from datetime import datetime, date, time

from models import CloseApproach
import config_values

"""
Does the tweeting of the close approach data
"""
class Tweeter:
  tweet_url = 'http://twitter.com/statuses/update.json'
  tweet_format = "At %s, an object named %s with diameter %dm just missed earth by %dkm, travelling at %dkm/s!"
  data_to_tweet = None
  data_manager = None

  """
  Expects data_to_tweet to be a list of CloseApproach objects
  """
  def __init__(self, data_to_tweet = None):
    self.data_to_tweet = data_to_tweet

  def send_tweet(self, ca):
    contents = self.tweet_format % (ca.approach_date, ca.object_name, ca.estimated_diameter, ca.minimum_distance_away, ca.relative_velocity)
    headers = { 'Authorization' : 'Basic %s' % self.encode_credentials() }
    data = urllib.urlencode({ 'status' : contents })
    request = urllib2.Request(self.tweet_url, data, headers)
    response = urllib2.urlopen(request)

  def encode_credentials(self):
    return base64.b64encode('%s:%s' % (config_values.twitter_username, config_values.twitter_password))

  """
  Tweet the data with which this Tweeter was initialised and save the 
  date tweeted for each close approach.
  """
  def tweet(self):
    if self.data_to_tweet != None and len(self.data_to_tweet) > 0:
      for ca in self.data_to_tweet:
        self.send_tweet(ca)
