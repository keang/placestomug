import os
import re
import random
import hashlib
import hmac
from string import letters
import datetime
from collections import namedtuple
from pytz.gae import pytz

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'TomMarvoloRiddle'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

class MainPage(Handler):
    def get(self):
        self.render("main-page.html")
    def post(self):
        action = self.request.get('Action')
        if action == 'create_shipment':
            self.redirect('/create_shipment')
        elif action == 'change_shipment_status':
            self.redirect('/change_shipment_status')
        elif action == 'deliver_shipment':
            self.redirect('/deliver_shipment')
        elif action == 'note_shipment_quality':
            self.redirect('/note_shipment_quality')
        elif action == 'view_shipment':
            self.redirect('/view_shipment_status')
        elif action == 'create_customer':
            self.redirect('/create_customer')
        elif action == 'view_customer':
            self.redirect('/view_customer')
        elif action == 'resolve_quality':
            self.redirect('resolve_quality')

class Shipment(db.Model):
    added_at = db.DateTimeProperty(auto_now_add = True)
    recipient = db.StringProperty(required = True)
    shipment_value = db.IntegerProperty(required = True)
    scheduled_delivery = db.DateProperty (auto_now_add = False)
    shipped_at = db.DateTimeProperty (auto_now_add = False)
    delivered_at = db.DateTimeProperty (auto_now_add = False)
    client_email = db.EmailProperty (required = False)
    client_phone = db.PhoneNumberProperty (required = False)
    shipped = db.BooleanProperty (required = True)
    delivered = db.BooleanProperty (required = True)
    on_time = db.BooleanProperty (required = False)
    quality_issue = db.BooleanProperty (required = False)
    quality_issue_desc = db.TextProperty (required = False)
    quality_issue_time_reported = db.DateTimeProperty (auto_now_add = False)
    quality_issue_resolved = db.BooleanProperty (required = False)
    quality_issue_resolved_time = db.DateTimeProperty (auto_now_add = False)
    quality_issue_resolved_desc = db.TextProperty (required = False)

class CreateShipment(Handler):
    def get(self):
        CustomerList = db.GqlQuery("SELECT * FROM Customer")
        l = []
        for e in CustomerList:
            l.append([e.key(),e.customer_name])
        self.render("create-shipment.html", l = l)
        
    def post(self):
        recipientID = self.request.get('CustomerName')
        query = db.GqlQuery("SELECT * FROM Customer where __key__ = KEY(:1)", recipientID)
        a = query.get()
        recipient = a.customer_name
        shipment_value = int(self.request.get('shipment_value'))
        a = self.request.get('scheduled_date').split('-')
        scheduled_delivery = datetime.date(int(a[0]), int(a[1]), int(a[2]))
        client_email = self.request.get('client_email')
        client_phone = self.request.get('client_phone')

        if client_email and client_phone:
            a = Shipment(recipient = recipient, shipment_value = shipment_value,
                     scheduled_delivery = scheduled_delivery,
                     client_email = client_email,
                     client_phone = client_phone,
                     shipped = False, delivered = False)
        elif client_email:
            a = Shipment(recipient = recipient, shipment_value = shipment_value,
                     scheduled_delivery = scheduled_delivery,
                     client_email = client_email,
                     shipped = False, delivered = False)
        elif client_phone:
            a = Shipment(recipient = recipient, shipment_value = shipment_value,
                     scheduled_delivery = scheduled_delivery,
                     client_phone = client_phone,
                     shipped = False, delivered = False)
        else:
            a = Shipment(recipient = recipient, shipment_value = shipment_value,
                     scheduled_delivery = scheduled_delivery,
                     shipped = False, delivered = False)
        a.put()
        self.redirect('/')

class ChangeShipmentStatus(Handler):
    def get(self):
        NotShippedList = db.GqlQuery("SELECT * FROM Shipment WHERE shipped = FALSE")
        l = []
        for e in NotShippedList:
            shipment = e
            l.append([shipment.key(),shipment.recipient+' '+str(shipment.scheduled_delivery)])
        self.render("change-shipment-status.html", l = l)

    def post(self):
        ShipmentID = self.request.get("ShipmentID") 
        shipped = self.request.get("shipped")
        if shipped == 'Yes':
            query = db.GqlQuery("SELECT * FROM Shipment where __key__ = KEY(:1)", ShipmentID)
            a = query.get()
            a.shipped = True
            a.shipped_at = datetime.datetime.now(pytz.timezone("Asia/Singapore"))
            a.put()
        self.redirect('/')

class DeliverShipment(Handler):
    def get(self):
        NotDeliveredList = db.GqlQuery("SELECT * FROM Shipment WHERE delivered = FALSE AND shipped = TRUE")
        l = []
        for e in NotDeliveredList:
            shipment = e
            l.append([shipment.key(),shipment.recipient+' '+str(shipment.scheduled_delivery)])
        self.render("change-delivery-status.html", l = l)

    def post(self):
        ShipmentID = self.request.get("ShipmentID") 
        delivered = self.request.get("delivered")
        if delivered == 'Yes':
            query = db.GqlQuery("SELECT * FROM Shipment where __key__ = KEY(:1)", ShipmentID)
            a = query.get()
            a.delivered = True
            a.delivered_at = datetime.datetime.now(pytz.timezone("Asia/Singapore"))
            if a.delivered_at.date() > a.scheduled_delivery:
                a.on_time = False
            else:
                a.on_time = True
            a.quality_issue = False
            a.put()
        self.redirect('/')

class ViewShipmentStatus(Handler):
    def get(self):
        ShipmentList = db.GqlQuery("SELECT * FROM Shipment")
        l = []
        for e in ShipmentList:
            shipment = e
            l.append([shipment.key(),shipment.recipient+' '+str(shipment.scheduled_delivery)])
        self.render("view-shipment-status.html", l = l)

    def post(self):
        ShipmentID = self.request.get("ShipmentID") 
        query = db.GqlQuery("SELECT * FROM Shipment where __key__ = KEY(:1)", ShipmentID)
        a = query.get()
        Recipient = a.recipient
        Value = a.shipment_value
        ScheduledDelivery = a.scheduled_delivery
        AddedAt = a.added_at
        ShippedAt = a.shipped_at
        DeliveredAt = a.delivered_at
        ClientEmail = a.client_email
        ClientPhone = a.client_phone
        OnTime = a.on_time
        Quality = a.quality_issue
        QualityDesc = a.quality_issue_desc
        QualityIssueTime = a.quality_issue_time_reported
        QualityIssueResolved = a.quality_issue_resolved
        QualityResolvedTime = a.quality_issue_resolved_time
        QualityResolvedDesc = a.quality_issue_resolved_desc
        self.render("view-shipment-status-2.html", Recipient = Recipient,
                    Value = Value, ScheduledDelivery = ScheduledDelivery,
                    AddedAt = AddedAt, ShippedAt = ShippedAt,
                    DeliveredAt = DeliveredAt, ClientEmail = ClientEmail,
                    ClientPhone = ClientPhone, OnTime = OnTime, Quality = Quality,
                    QualityDesc = QualityDesc, QualityIssueTime = QualityIssueTime,
                    QualityIssueResolved = QualityIssueResolved, QualityResolvedTime = QualityResolvedTime, 
                    QualityResolvedDesc = QualityResolvedDesc)

class NoteShipmentQuality(Handler):
    def get(self):
        QualityIssueList = db.GqlQuery("SELECT * FROM Shipment WHERE delivered = TRUE AND quality_issue = FALSE")
        l = []
        for e in QualityIssueList:
            shipment = e
            l.append([shipment.key(),shipment.recipient+' '+str(shipment.scheduled_delivery)])
        self.render("note-shipment-quality.html", l = l)

    def post(self):
        ShipmentID = self.request.get("ShipmentID")
        query = db.GqlQuery("SELECT * FROM Shipment where __key__ = KEY(:1)", ShipmentID)
        a = query.get()
        qualityS = self.request.get("issue")
        quality_issue_desc = self.request.get("QualityDesc")
        if qualityS == 'Yes, there were issues':
            quality_issue = True
            a.quality_issue_resolved = False
        else:
            quality_issue = False
        a.quality_issue = quality_issue
        a.quality_issue_desc = quality_issue_desc
        a.quality_issue_time_reported = datetime.datetime.now(pytz.timezone("Asia/Singapore"))
        a.put()
        self.redirect('/')

class ResolveQuality(Handler):
    def get(self):
        ShipmentWithIssuesList = db.GqlQuery("SELECT * FROM Shipment WHERE quality_issue = TRUE AND quality_issue_resolved = FALSE")
        l = []
        for shipment in ShipmentWithIssuesList:
            l.append([shipment.key(),shipment.recipient+' '+str(shipment.quality_issue_time_reported)])
        self.render("resolve-quality.html", l = l)

    def post(self): 
        ShipmentID = self.request.get("ShipmentID") 
        resolved = self.request.get("resolved")
        resolvedDesc = self.request.get("resolvedDesc")
        if resolved == 'Yes':
            query = db.GqlQuery("SELECT * FROM Shipment where __key__ = KEY(:1)", ShipmentID)
            a = query.get()
            a.quality_issue_resolved = True
            a.quality_issue_resolved_time = datetime.datetime.now(pytz.timezone("Asia/Singapore"))
            a.quality_issue_resolved_desc = resolvedDesc
            a.put()
        self.redirect('/view_shipment_status')


class Customer(db.Model):
    customer_name = db.StringProperty (required = True)
    total_revenue = db.IntegerProperty (required = True)
    satisfaction_index = db.IntegerProperty (required = False)

class CreateCustomer(Handler):
    def get(self):
        self.render("create-customer.html")
    def post(self):
        customer_name = self.request.get('company_name')
        total_revenue = int(self.request.get('total_revenue'))
        a = Customer(customer_name = customer_name, total_revenue = total_revenue)
        a.put()
        self.redirect('/')

class ViewCustomer(Handler):
    def get(self):
        self.write("Page under construction!")
        
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/create_shipment', CreateShipment),
                               ('/change_shipment_status', ChangeShipmentStatus),
                               ('/deliver_shipment', DeliverShipment),
                               ('/view_shipment_status', ViewShipmentStatus),
                               ('/note_shipment_quality', NoteShipmentQuality),
                               ('/create_customer', CreateCustomer),
                               ('/view_customer', ViewCustomer),
                               ('/resolve_quality', ResolveQuality)],
                               debug=True)
