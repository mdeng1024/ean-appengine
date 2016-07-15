#!/usr/bin/env python

# [START imports]
import os
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

from eanclient import EanClient
from eanclient import Hotel

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]


# [START Models]
# http://stackoverflow.com/questions/3777367/what-is-a-good-place-to-store-configuration-in-google-appengine-python
class Configuration(ndb.Model):
    name = ndb.StringProperty()
    value = ndb.StringProperty()

    @staticmethod
    def get(name):
        NOT_SET_VALUE = "NOT SET"
        retval = Configuration.query(Configuration.name == name).get()
        if not retval:
            retval = Configuration()
            retval.name = name
            retval.value = NOT_SET_VALUE
            retval.put()
        if retval.value == NOT_SET_VALUE:
            raise Exception(('Setting %s not found in the database. A placeholder ' +
                             'record has been created. Go to the Developers Console for your app ' +
                             'in App Engine, look up the Settings record with name=%s and enter ' +
                             'its value in that record\'s value field.') % (name, name))
        return retval.value


class Account(ndb.Model):
    """Sub model for representing a user"""
    email = ndb.StringProperty(indexed=True)
    role = ndb.IntegerProperty(indexed=False)
    id = email

# [END Models]


# [START Initialization]

# Define the criteria used to connect to EAN
cid = Configuration.get("cid");
apiKey = Configuration.get("apiKey");
secret = Configuration.get("secret");
mapKey = Configuration.get("mapKey");

ean_client = EanClient(cid, apiKey, secret)

# [END Initialization]



# Secured Request Handling
class SecuredRequestHanlder(webapp2.RequestHandler):

    def process_request(self):
        raise NotImplementedError()

    def allow_access(self):
        if not users.IsCurrentUserAdmin():
            user = users.get_current_user()
            account = Account._get_by_id(user.email())
            if not account:
                # no such user exists
                return False
        return True

    def get(self):
        self.post()

    def post(self):
        if self.allow_access():
            self.process_request()
        else:
            message = "You are not allowed to access this application, please contact your administrator for access"
            template_values = {
                'message': message
            }

            template = JINJA_ENVIRONMENT.get_template('error.html')
            self.response.write(template.render(template_values))


# [START main_page]
class MainPage(SecuredRequestHanlder):

    def process_request(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            # self.redirect(url_linktext)

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]


# [START hotelListing]
class ListHotels(SecuredRequestHanlder):

    def process_request(self):
        parameters = {'arrivalDate': self.request.get('checkInDate'),
                      'departureDate': self.request.get('checkOutDate')}

        rooms = int(self.request.get('rooms'))
        adults = int(self.request.get('adults'))

        if rooms > 1:
            people_count = int(adults / rooms)
            remain_people = adults - people_count * rooms
            room_label = None
            for i in range(rooms):
                room_label = 'room' + str(i + 1)
                parameters[room_label] = people_count
            if remain_people > 0:
                parameters[room_label] += remain_people
        else:
            parameters['room1'] = adults

        room_parameters = parameters.copy()

        paging = self.request.get('paging')
        # logging.info('paging:' + paging)
        if paging != 'true':
            ean_client.resetPreviousCache()

            destination = self.request.get('destination').split(',')
            parameters['city'] = destination[0]
            # parameters['stateProvinceCode'] = 'NW'
            parameters['countryCode'] = destination[1]
            parameters['minStarRating'] = self.request.get('rating')
        else:
            parameters.clear()

        logging.debug(parameters)

        hotels = ean_client.hotleList(parameters)

        template_values = {
            'hotels': hotels,
            'more': ean_client.paging,
            'parameters': room_parameters
        }

        template = JINJA_ENVIRONMENT.get_template('hotellist.html')
        self.response.write(template.render(template_values))

# [END hotelListing]

class HotelInfo(SecuredRequestHanlder):

    def process_request(self):
        parameters = {'hotelId': self.request.get('hotelId')}
        # parameters['options'] = 'HOTEL_SUMMARY,HOTEL_DETAILS,HOTEL_IMAGES'

        hotel = ean_client.hotelInfo(parameters)

        parameters.clear()
        parameters['hotelId'] = self.request.get('hotelId')
        ean_client.roomImages(parameters, hotel.rooms)

        template_values = {
            'hotel': hotel,
            'mapKey': mapKey
        }

        template = JINJA_ENVIRONMENT.get_template('hotelInfo.html')
        self.response.write(template.render(template_values))

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/listhotels', ListHotels),
    ('/hotelinfo', HotelInfo),
], debug=False)
# [END app]
