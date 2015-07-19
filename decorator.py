import functools
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import os.path

from operator import itemgetter
from tornado.options import define, options
import webbrowser


import Settings
import tornado.escape

def protected(method):
    @tornado.web.authenticated
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Expires', '0' )

        return method(self, *args, **kwargs)
    return wrapper
