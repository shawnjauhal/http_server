# http_server

Author: Shawn Jauhal
Date: October 31st, 2020

Written for Python 3.7  
Dependencies:
Pandas, GeoIP(python3), geolite2, requests(testing only)

Install the following libraries:  
pip install pandas  
pip install python-geoip-python3   
pip install python-geoip-geolite2   
pip install requests

Class: Server

This class represents a http service which takes three possible formats for GET requests.

1.
/collect?cid=<UUID>
This requests responds with a 200 and no body.  The server populates the database with uuid's and the date they 
submitted this request, it also takes the corresponding country code of the client.  The uuid is in hexadecimal
with format 8-4-4-4-12

2.
/uniques?d=<date>
This request responds with a list of uuid's from users that logged in on the given date.

3.
/uniques?d=<date>&cc=<2 character ISO country code>
This request responds just like the previous request, but it allows the client to filter uuid's by their corresponding
country code in the table.

The header submits the HTTP_X_FORWARDED_FOR which is the client's ip address

Important note: all the dates are in the format YYYY-MM-DD and based on GMT

------------------------------------------------------------------------------------------------------------------------

Database: UUIDLog.db

This contains a database that logs UUID's.  It's first column contains each UUID that has been logged on ther server. 
The following column represents the two character country code obtained from the clients ip address and GeoIP.  
The rest of the columns represent each date the server was obtaining data from the user.  If the value is 1 then the 
UUID had logged in on that day, otherwise the value is 0.

------------------------------------------------------------------------------------------------------------------------

Testing: 
Class: TestServer

This class was used on my localhost alongside a google cloud platform vm running the server with a static ip address.  
It tests the basic functionality of the server.  The IP address and port number may change depending on the machine
running the server code being tested.
