import os
import re
from string import letters
import datetime
from collections import namedtuple

import webapp2
import jinja2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
#        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Place(db.Model):
    faculty = db.StringProperty (required = True)
    area = db.StringProperty (required = True)
    vote = db.IntegerProperty(required = True)

class MainPage(Handler):
    def get(self):

        #facs = ["Arts", "Business", "Central Library", "Computing" ,"Science", "SDE", "Engin", "Medicine", "Music", "UTown"]
        #for f in facs:
         #   newItem = Faculty(key_name=f, facultyName=f)
         #   newItem.put()
        
        places = db.GqlQuery("SELECT * FROM Place ORDER BY vote DESC")

        facultiesList = {}        
        for p in places.run(): 
            facultiesList[p.faculty] = p.faculty

      #  places = db.GqlQuery("SELECT * FROM Place ORDER BY vote DESC")
         
        self.render("form.html", faculties = facultiesList, places=places)
        #self.render("test.html")
    
        
class AddPlace(Handler):
    def get(self):
        """faculty = self.request.get('selected_faculty').lower()
        area = self.request.get('selected_area').lower()
        akey = db.Key.from_path('Place', faculty+area)
        a = db.get(akey)
        
        if a==None:
            a = Place(key_name= faculty+area, faculty = faculty, area = area, vote=1)
            a.put()
        else:
            a.vote = a.vote + 1
            a.put()   """
        self.write("YAY") 
        #self.redirect('/')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/fac', AddPlace)],
                               debug=True)
