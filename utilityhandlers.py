
import sys, os
import traceback
import re
import math
import urllib, urllib2
from datetime import datetime, date, time

from google.appengine.ext import db
from google.appengine.ext import webapp

from BeautifulSoup import BeautifulSoup
from models import CloseApproach

class MarkAsTweetedHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write("""
      <html>
        <body>
          <form action="/markastweeted" method="post">
            Mark any close approaches with an approach date less than (yyyy-mm-dd hh:mm):
            <div><input type="text" name="boundary" /></div>
            as tweeted at (yyyy-mm-dd hh:mm):
            <div><input type="text" name="tweet_date" /></div>
            <div><input type="submit" value="Go." /></div>
          </form>
        </body>
      </html>""")

  def post(self):
    boundary = datetime.strptime(self.request.get('boundary'), '%Y-%m-%d %H:%M')
    tweet_date = datetime.strptime(self.request.get('tweet_date'), '%Y-%m-%d %H:%M')
    query ='SELECT * FROM CloseApproach WHERE approach_date < :boundary AND date_tweeted = NULL'
    data = db.GqlQuery(query, boundary = boundary)
    for ca in data:
      ca.date_tweeted = tweet_date
      ca.put()
    self.response.out.write('Updated %d CloseApproach entities as tweeted at %s' % (data.count(), tweet_date))

class LoadHistoricalHandler(webapp.RequestHandler):
  plus_minus_char = unichr(177).encode('latin-1')
  data_file = 'data/full-history-20100212.html'

  def get(self):
    self.response.out.write("""
      <html>
        <body>
          <form action="/loadhistorical" method="post">
            Load all historical data as being tweeted at (yyyy-mm-dd hh:mm):
            <div><input type="text" name="tweet_date" /></div>
            <div><input type="submit" value="Go." /></div>
          </form>
        </body>
      </html>""")

  def post(self):
    tweet_date = datetime.strptime(self.request.get('tweet_date'), '%Y-%m-%d %H:%M')
    query = 'SELECT * FROM CloseApproach ORDER BY approach_date ASC LIMIT 1'
    try:
      result = db.GqlQuery(query).get()
    except:
      result = None
    if result:
      older_than = result.approach_date
      data = self.get_historical_data(older_than)
      for ca in data:
        ca.date_tweeted = tweet_date
        ca.put()
      self.response.out.write('Inserted %d new CloseApproach entities as tweeted at %s' % (len(data), tweet_date))
    else:
      self.response.out.write('Some kind of crazy thing happened!!!')

  def get_historical_data(self, older_than):
    results = []
    try:
      path = os.path.join(os.path.dirname(__file__), self.data_file)
      f = open(path, 'r')
      soup = BeautifulSoup(f.read())
      rows = soup.find('table', { 'cellspacing' : '0', 'cellpadding' : '2', 'border' : '1' }).contents
      del rows[0] # Strip the header row
      for r in rows:
        if hasattr(r, 'contents'):
          ca = self.get_close_approach_from_row(r)
          if ca != None and ca.approach_date < older_than:
            results.append(ca)
    except:
      self.response.out.write('Problem parsing close approach data from %s <br /><pre>%s</pre>' % (self.data_file, self.format_exception()))
    return results

  def get_close_approach_from_row(self, row):
    ca = None
    if row != None:
      name, date, dist, velo, diam = None, None, None, None, None
      try:
        # Parse out the values to construct a CloseApproach object
        name = str(row.contents[1].contents[0].string).replace('&nbsp;', ' ').strip(' ()')
        date_match = re.match('(.*)&plusmn;.*', str(row.contents[3].contents[0].string).replace('&nbsp;', ' ').strip())
        if date_match != None:
          date = datetime.strptime(date_match.group(1).strip(), '%Y-%b-%d %H:%M')
        dist_match = re.match('^(.*)/.*$', str(row.contents[7].contents[0].string).strip())
        if dist_match != None:
          dist = float(dist_match.group(1)) * 384000
        velo = str(row.contents[9].contents[0].string).strip()
        diam = self.absmag_to_diam(float(str(row.contents[15].contents[0].string).strip()), 0.25)
        if name != None and date != None and dist != None and velo != None and diam != None:
          ca = CloseApproach(object_name = name, approach_date = date, minimum_distance_away = int(dist),
          relative_velocity = round(float(velo), 2), estimated_diameter = int(diam))
      except:
        ca = None
    return ca

  """
  Utility function to convert Absolute Magnitude to Diameter in metres for Minor Planets
  Adapted from: http://www.physics.sfasu.edu/astro/asteroids/sizemagnitude.html
  """
  def absmag_to_diam(self, absmag, albedo):
    ee = -0.2 * absmag;
    d = math.floor(1000 * (1329 / math.pow(albedo,0.5)) * math.pow(10, ee));
    return d

  """
  Utility function to format exception info
  """
  def format_exception(self, maxTBlevel = 5):
    cla, exc, trbk = sys.exc_info()
    excName = cla.__name__
    try:
      excArgs = exc.__dict__["args"]
    except KeyError:
      excArgs = "<no args>"
    excTb = traceback.format_tb(trbk, maxTBlevel)
    return (excName, excArgs, excTb)
