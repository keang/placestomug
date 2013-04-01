import os
import re
from string import letters
import datetime
from collections import namedtuple

import webapp2
import jinja2
import json

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


places = db.GqlQuery("SELECT * FROM Place ORDER BY vote DESC")


class MainPage(Handler):
    def get(self):
        facultiesList = {}        
        for p in places.run(): 
            facultiesList[p.faculty] = p.faculty

        self.render("form2.html", faculties=facultiesList, places = places)
        #self.render("test.html")
    
class GetFaculty(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        facList = {}
        for p in places.run():
            facList[p.faculty] = p.faculty        
        distinctFacList = []
        for f in facList:
            distinctFacList.append({"faculty_name":f})

        self.response.out.write(json.dumps(distinctFacList))

class GetArea(Handler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        areaList = []
        for p in places.run():
            if p.faculty == self.request.get('selected_faculty'):
                areaList.append({"area_name":p.area})
        
        self.response.out.write(json.dumps(areaList))

class AddAreaHandler(Handler):
    def post(self):
        faculty = self.request.get('selectedFaculty')
        newArea = self.request.get('areaToSubmit')
        akey = db.Key.from_path('Place', faculty+newArea)
        a = db.get(akey)
        if a==None:
            a = Place(key_name= faculty+newArea, faculty = faculty, area = newArea, vote=1)
            a.put()
        else:
            a.vote = a.vote + 1
            a.put() 
        self.redirect('/')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/getarea', GetArea), 
                               ('/getfaculty', GetFaculty),
                               ('/addarea', AddAreaHandler)
                               ], debug=True)
