
from google.appengine.ext import db
from google.appengine.tools import bulkloader

class CloseApproachExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'CloseApproach',
                                     [('object_name', str, None),
                                      ('approach_date', str, None),
                                      ('minimum_distance_away', str, None),
                                      ('relative_velocity', str, None),
                                      ('estimated_diameter', str, None),
                                      ('date_added', str, None),
                                      ('date_tweeted', str, None)
                                     ])

exporters = [CloseApproachExporter]
