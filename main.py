#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from handlers import MainHandler
from handlers import CloseApproachDetailHandler
from handlers import RssHandler
from handlers import ScrapeHandler
from handlers import MarkAsTweetedHandler

def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
    ('/misses/(.*)', CloseApproachDetailHandler),
    ('/rss', RssHandler),
    ('/scrape', ScrapeHandler),
    ('/markastweeted', MarkAsTweetedHandler)], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
