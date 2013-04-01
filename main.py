import os
import re
from string import letters
import datetime
from collections import namedtuple
import logging

import webapp2
import jinja2
import json

from google.appengine.ext import db
from google.appengine.api import memcache

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
        #params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Place(db.Model):
    faculty = db.StringProperty (required = True)
    area = db.StringProperty (required = True)
    vote = db.IntegerProperty(required = True)

class MainPage(Handler):
    def get_places(self):

        placesList = memcache.get("top")
        if placesList is not None:
            return placesList
        else:
            places = db.GqlQuery("SELECT * FROM Place ORDER BY faculty DESC")
            placesList = list(places)
            memcache.add("top", placesList)
            
            return placesList 


    def get(self):
        placesList = self.get_places()
        facultiesList = {}        
        for p in placesList: 
            self.write(p)
            facultiesList[p.faculty] = p.faculty
        facultiesList["Engineering"] = "Engineering"
        self.render("form2.html", faculties=facultiesList, places = placesList)
        #self.render("test.html")

class AddAreaHandler(Handler):
    def post(self):
        faculty = self.request.get('selectedFaculty')
        newArea = self.request.get('areaToSubmit')
        akey = db.Key.from_path('Place', faculty+newArea)
        a = db.get(akey)
        
        if a==None:
            a = Place(key_name= faculty+newArea, faculty = faculty, area = newArea, vote=1)
            
        else:
            a.vote = a.vote + 1
        a.put() 
        self.update_memcache(a)
        self.redirect('/')

    def update_memcache(self, newPlace):
        client = memcache.Client()
        updatedCache = client.get("top")

        #new cache image:
        updatedCache.append(newPlace)

        #retury loop:
        while True:
            tryList = client.gets("top")
            assert tryList is not None, 'Uninitialized counter'
            if client.cas("top", updatedCache):
                logging.error("Wrote cache")
                break

    
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


class ServerErrorPage(Handler):
    def get(self):
        self.render("serverbusy.html")


fac = ''
area=''
class ChopSeatHandler(Handler):

    def get(self):
        self.render("chopseat.html", fac=fac, area=area)
    def post(self):
        global fac
        global area
        fac = self.request.get("fac")
        area = self.request.get("area")
        self.redirect('/chopseat')

class ShowTicketHandler(Handler):
    def get(self):
        name = self.request.get("fullname")
        self.render("ticket.html", name=name, fac=fac, area=area)

app = webapp2.WSGIApplication([('/', MainPage),
                                ('/serverbusy', ServerErrorPage),
                               ('/getarea', GetArea), 
                               ('/getfaculty', GetFaculty),
                               ('/addarea', AddAreaHandler),
                               ('/chopseat', ChopSeatHandler),
                               ('/showticket', ShowTicketHandler)
                               ], debug=True)
