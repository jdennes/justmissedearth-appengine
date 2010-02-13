#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from handlers import MainHandler
from handlers import CloseApproachDetailHandler
from handlers import FeedHandler
from handlers import ScrapeHandler

# Utility handlers
from utilityhandlers import MarkAsTweetedHandler
from utilityhandlers import LoadHistoricalHandler

def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
    ('/misses', MainHandler),
    ('/misses/(.*)', CloseApproachDetailHandler),
    ('/feed', FeedHandler),
    ('/scrape', ScrapeHandler),
    ('/markastweeted', MarkAsTweetedHandler),
    ('/loadhistorical', LoadHistoricalHandler)], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
