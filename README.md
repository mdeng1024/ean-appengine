# ean-appengine

EAN API Test program. Using Google's Python [Guestbook][8] as the startup project. This project uses [EAN API][9] to perform basic hotel search and hotel detail information retrieval. Google map API is also used to display hotel's location on the Map.  

## Datastore setup
This application require storing EAN configuration (_cid_, _apiKey_, _secret_) and Google Map Key (_mapKey_) in the datastore. Once application is run locally or deployed to AppEngine, go to datastore view page create new _Configuration_ enity and add these values as entries. 

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [NDB Datastore API][3]
- [Users API][4]

## Dependencies
- [webapp2][5]
- [jinja2][6]
- [Twitter Bootstrap][7]

[1]: https://developers.google.com/appengine
[2]: https://python.org
[3]: https://developers.google.com/appengine/docs/python/ndb/
[4]: https://developers.google.com/appengine/docs/python/users/
[5]: http://webapp-improved.appspot.com/
[6]: http://jinja.pocoo.org/docs/
[7]: http://twitter.github.com/bootstrap/
[8]: https://github.com/GoogleCloudPlatform/appengine-guestbook-python
[9]: http://developer.ean.com/docs/
