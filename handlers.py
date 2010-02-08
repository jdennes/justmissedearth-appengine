
import sys, os
import traceback
import re
import math
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
from datetime import datetime, date, time

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from models import CloseApproach

class MainHandler(webapp.RequestHandler):

  def get(self):
    query = CloseApproach.all().order('-approach_date')
    close_approaches = query.fetch(20)
    values = {
      'close_approaches': close_approaches
    }
    path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.out.write(template.render(path, values))

class ScrapeHandler(webapp.RequestHandler):
  
  data_url = "http://neo.jpl.nasa.gov/cgi-bin/neo_ca?type=NEO&hmax=all&sort=date&sdir=DESC&tlim=recent_past&dmax=10LD&max_rows=20&action=Display+Table&show=1"
  data_pattern = r'<font size="-1" face="courier, monospace">(.*)</font>'

  def get(self):
    self.response.out.write('Consolidation started. <br />')
    self.consolidate()
    self.response.out.write('Consolidation finished. <br />')
    
    # TODO: Add tweeting as @justmissedearth

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

  """
  Consolidates the local data store so that it is up-to-date with the latest
  data from NASA
  """
  def consolidate(self):
    past_approaches = self.retrieve_past_close_approaches_data()
    last_saved_approach_date = self.get_latest_saved_approach_date()
    save_count = 0

    if last_saved_approach_date:
      # Only save approaches which have not yet been saved
      for a in past_approaches:
        # Check approach date and only save if it is greater than the last saved approach date
        if a.approach_date > last_saved_approach_date:
          a.put()
          save_count += 1
    else:
      # Save all past approaches retrieved
      for a in past_approaches:
        a.put()
        save_count += 1
    self.response.out.write('Wrote %d past approaches to the data store.<br />' % save_count)

  """
  Retrieves only past data from NASA
  """
  def retrieve_past_close_approaches_data(self):
    results = []
    try:
      response = urllib2.urlopen(self.data_url)
      soup = BeautifulSoup(response.read())
      rows = soup.find('table', { 'cellspacing' : '0', 'cellpadding' : '2', 'border' : '1' }).contents
      del rows[0] # Strip the header row
      for r in rows:
        if hasattr(r, 'contents'):
          ca = self.get_close_approach_from_row(r)
          if ca != None:
            results.append(ca)
    except:
      self.response.out.write('Problem parsing close approach data from %s <br /><pre>%s</pre>' % (self.data_url, self.format_exception()))
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
  Retrieves the latest approach date which has been saved to our data store
  """
  def get_latest_saved_approach_date(self):
    result = None
    query = 'SELECT * FROM CloseApproach ORDER BY approach_date DESC LIMIT 1'
    try:
      result = db.GqlQuery(query).get()
    except:
      result = None
    if result:
      return result.approach_date
    return None

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