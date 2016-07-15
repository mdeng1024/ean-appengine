# Testing out Expedia REST hotel booking APIs
import urllib
import hashlib
import time
import json
import logging

from HTMLParser import HTMLParser

# https://book.api.ean.com/api/tester/
imageBase = 'http://media.expedia.com'


class Room(object):
    def __init__(self, typeId, name):
        self.id = typeId
        self.type_code = None
        self.name = name    # short description
        self.description = None
        self.image_url = None
        self.amenity = []


class Hotel(object):
    def __init__(self, hotelId, name, address, rating=None):
        self.id = hotelId
        self.name = name
        self.rating = rating
        self.address = address
        self.city = ''
        self.province = ''
        self.post_code = ''
        self.latitude = None
        self.longitude = None
        self.imageUrl = None
        self.roomDescription = None
        self.totalRate = None
        self.valueAdds = []
        self.images = []
        self.rooms = []

    def imageSize(self):
        return len(self.images)

    def addImage(self, imageUrl):
        self.images.append(imageUrl)

    def addValueAdd(self, valueAdd):
        self.valueAdds.append(valueAdd)


class EanClient(object):
    def __init__(self, cid, apiKey, secret, locale="en_US", currencyCode="USD"):
        self.service = 'http://api.ean.com/ean-services/rs/hotel/'
        self.version = 'v3/'
        self.cid = cid
        self.apiKey = apiKey
        self.secret = secret
        self.customerSessionId = None
        self.cacheKey = None
        self.cacheLocation = None
        self.locale = locale    # http://developer.ean.com/general-info/hotel-language-options/
        self.currencyCode = currencyCode
        self.paging = False
        self.commonParameters = {'cid': self.cid,
                                 'apiKey': self.apiKey,
                                 # 'minorRev': "[x]",
                                 # 'customerUserAgent': '[xxx]',
                                 # 'customerIpAddress': '[xxx]',
                                 'locale': self.locale,
                                 'currencyCode': self.currencyCode}

    def resetPreviousCache(self):
        self.paging = False
        self.cacheKey = None
        self.cacheLocation = None
        self.last_used_url = None

    def updateSig(self, parameters):
        # seconds since GMT Epoch
        timestamp = str(int(time.time()))
        sig = hashlib.md5(self.apiKey + self.secret + timestamp).hexdigest()
        parameters['sig'] = sig

    def connect_ean(self, method, parameters):
        self.updateSig(parameters)
        if self.customerSessionId is not None:
            parameters['customerSessionId'] = self.customerSessionId
        parameters.update(self.commonParameters)
        url = self.service + self.version + method + '?' + urllib.urlencode(parameters)
        logging.info(url)

        try:
            response = urllib.urlopen(url)
            # logging.debug(response.read())
            msg = json.load(response)
            # logging.debug(msg)
            return msg
        except Exception as e:
            logging.error('EAN API "{0}" call encountered error: {1}'.format(method, e.message))
            raise e



    def hotleList(self, parameters):
        # http://developer.ean.com/docs/hotel-list/examples/rest-basic-availability/
        method = 'list/'
        if self.paging and self.cacheKey is not None and self.cacheLocation is not None:
            parameters.clear()
            parameters['supplierType'] = 'E'
            parameters['cacheKey'] = self.cacheKey
            parameters['cacheLocation'] = self.cacheLocation

        msg = self.connect_ean(method, parameters)

        hotels = []

        if "HotelListResponse" in msg:
            resp = msg["HotelListResponse"]
            if "customerSessionId" in resp:
                self.customerSessionId = resp["customerSessionId"]
            if 'EanWsError' in resp:
                error = resp['EanWsError']
                logging.error("Encountered Error: " + error['handling'] + ' - ' + error['category'] + ': ' + error['verboseMessage'])
            elif 'HotelList' in resp:
                if 'cacheKey' in resp and 'moreResultsAvailable' in resp:
                    self.paging = resp['moreResultsAvailable']
                    self.cacheKey = resp['cacheKey']
                    self.cacheLocation = resp['cacheLocation']
                else:
                    self.paging = False
                    self.cacheKey = None
                    self.cacheLocation = None

                hotelList = resp['HotelList']
                logging.debug('Showing hotle found: ' + hotelList['@size'] + '/' + hotelList['@activePropertyCount'])
                for hotel in hotelList['HotelSummary']:
                    logging.debug(str(hotel['hotelId']) + '\t' + hotel['name'] + '\t' + hotel['address1'] + '\t' + hotel['city'] + '\t' + str(hotel['hotelRating']))
                    hotelObj = Hotel(hotel['hotelId'], hotel['name'], hotel['address1'], hotel['hotelRating'])
                    hotelObj.city = hotel['city']
                    if 'stateProvinceCode' in hotel:
                        hotelObj.province = hotel['stateProvinceCode']
                    if 'postalCode' in hotel:
                        hotelObj.post_code = hotel['postalCode']
                    hotelObj.imageUrl = imageBase + hotel['thumbNailUrl']
                    hotelObj.latitude = hotel['latitude']
                    hotelObj.longitude = hotel['longitude']
                    if 'RoomRateDetailsList' in hotel:
                        hotelObj.roomDescription = hotel['RoomRateDetailsList']['RoomRateDetails']['roomDescription']
                        hotelObj.totalRate = \
                            hotel['RoomRateDetailsList']['RoomRateDetails']['RateInfos']['RateInfo']['ChargeableRateInfo']['@currencyCode'] \
                            + ' ' + \
                            hotel['RoomRateDetailsList']['RoomRateDetails']['RateInfos']['RateInfo']['ChargeableRateInfo']['@total']
                        # if 'ValueAdds' in hotel['RoomRateDetailsList']['RoomRateDetails']:
                        #     valueAdd = hotel['RoomRateDetailsList']['RoomRateDetails']['ValueAdds']['ValueAdd']['description']
                        #     hotelObj.addValueAdd(valueAdd)
                    hotels.append(hotelObj)
        else:
            logging.error("Unexpected response: " + msg)

        return hotels


    def hotelInfo(self, parameters):
        # http://developer.ean.com/docs/hotel-info/examples/rest-default-content/
        method = 'info/'

        msg = self.connect_ean(method, parameters)

        hotel = None

        if "HotelInformationResponse" in msg:
            resp = msg["HotelInformationResponse"]
            if "customerSessionId" in resp:
                self.customerSessionId = resp["customerSessionId"]
            if 'EanWsError' in resp:
                error = resp['EanWsError']
                logging.error("Encountered Error: " + error['handling'] + ' - ' + error['category'] + ': ' + error['verboseMessage'])
            elif 'HotelSummary' in resp:
                hotelSum = resp['HotelSummary']
                logging.debug(str(hotelSum['hotelId']) + '\t' + hotelSum['name'] + '\t' + hotelSum['address1'] + '\t' + str(hotelSum['hotelRating']))
                hotel = Hotel(hotelSum['hotelId'], hotelSum['name'], hotelSum['address1'], hotelSum['hotelRating'])
                hotel.longitude = hotelSum['longitude']
                hotel.latitude = hotelSum['latitude']
                hotelDetail = resp['HotelDetails']
                # logging.debug('\tFloor: ' + str(hotelDetail['numberOfFloors']) + ', Rooms: ' + str(hotelDetail['numberOfRooms']) + ', CheckOut: ' + hotelDetail['checkOutTime'])
                # logging.debug('\tExtra Information: ' + hotelDetail['propertyInformation'])
                hotel.roomDescription =  HTMLParser().unescape(hotelDetail['propertyDescription'])

                if 'HotelImages' in resp:
                    hotelImages = resp['HotelImages']
                    count = 0
                    for hotelImage in hotelImages['HotelImage']:
                        if count > 10: break
                        logging.debug(hotelImage['url'])
                        hotel.addImage(hotelImage['url'])
                        count += 1

                for room_type in resp['RoomTypes']['RoomType']:
                    room = Room(room_type['@roomTypeId'], room_type['description'])
                    room.type_code = room_type['@roomCode']
                    if 'descriptionLong' in room_type:
                        room.description = room_type['descriptionLong']
                    else:
                        room.description = room_type['description']

                    for amenity in room_type['roomAmenities']['RoomAmenity']:
                        room.amenity.append(amenity['amenity'])

                    hotel.rooms.append(room)

        else:
            logging.error("Unexpected response: " + msg)

        return hotel


    def roomImages(self, parameters, rooms):
        method = 'roomImages/'

        msg = self.connect_ean(method, parameters)

        if 'HotelRoomImageResponse' in msg:
            if 'RoomImages' in msg['HotelRoomImageResponse']:
                room_images = msg['HotelRoomImageResponse']['RoomImages']['RoomImage']
                for room_image in room_images:
                    logging.debug('roomTypeCode: ' + str(room_image['roomTypeCode']) + ', url: ' + room_image['url'])
                    for room in rooms:
                        if int(room.type_code) == room_image['roomTypeCode']:
                            room.image_url = room_image['url']
                            logging.debug(room.image_url)
        else:
            logging.error("Unexpected response: " + msg)


    def hotelRooms(self, parameters):
        method = 'avail/'

        parameters['includeRoomImages'] = 'true'
        parameters['options'] = 'HOTEL_DETAILS,ROOM_TYPES,ROOM_AMENITIES,HOTEL_IMAGES'

        msg = self.connect_ean(method, parameters)

        hotel = None

        if 'HotelRoomAvailabilityResponse' in msg:
            logging.debug(msg)
            hotelInfo = msg['HotelRoomAvailabilityResponse']
            hotel = Hotel(hotelInfo['hotelId'], hotelInfo['hotelName'], hotelInfo['hotelAddress'])
            hotel.city = hotelInfo['hotelCity']
            hotel.province = hotelInfo['hotelStateProvince']

            hotelDetails = hotelInfo['HotelDetails']
            hotel.roomDescription =  HTMLParser().unescape(hotelDetails['propertyDescription'])

            if 'HotelImages' in hotelInfo:
                hotelImages = hotelInfo['HotelImages']
                count = 0
                for hotelImage in hotelImages['HotelImage']:
                    if count > 10: break
                    logging.debug(hotelImage['url'])
                    hotel.addImage(hotelImage['url'])
                    count += 1

            if 'HotelRoomResponse' in hotelInfo:
                hotelRoom = hotelInfo['HotelRoomResponse']
                room = Room(hotelRoom['RoomType']['@roomTypeId'], hotelRoom['RoomType']['description'])
                room.type_code = hotelRoom['RoomType']['@roomCode']

                for amenity in hotelRoom['RoomType']['roomAmenities']['RoomAmenity']:
                    room.amenity.append(amenity['amenity'])

                if 'RoomImages' in hotelRoom:
                    room_images = hotelRoom['RoomImages']['RoomImage']
                    room.image_url = room_images[0]['url']  # we taking the first image
                    logging.debug(room.image_url)

                hotel.rooms.append(room)

        else:
            logging.error("Unexpected response: " + msg)

        return hotel
