import re
import sqlite3
import pandas
import threading
import time
import socket
from pandas.io import sql
from geoip import geolite2
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

"""
Author: Shawn Jauhal
Date: October 31st, 2020
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
"""

mutex_lock = threading.Lock()


class Server(BaseHTTPRequestHandler):

    def do_HEAD(self):
        """
        Sends http header, with content-type and HTTP_X_FORWARDED_FOR which includes the client ip address
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("HTTP_X_FORWARDED_FOR", self.client_address[0])
        self.end_headers()

    def do_GET(self):
        """
        Handles GET requests from the user based on the two handled endpoint paths
        """
        "Handle http header"

        # Gets the 2 character country code based on the users ip address
        country_code = geolite2.lookup(self.client_address[0]).country
        # Determine which endpoint the user is requesting
        collect_match = re.match(r'^/collect\?cid=(.*)$', self.path)
        unique_match = re.match(r'^/uniques\?d=(.*)$', self.path)
        if self.path == "/":
            self.do_HEAD()
        elif collect_match:
            self.handle_collect(self.path.split('=')[1], country_code)
            self.do_HEAD()
        elif unique_match:
            # Starts the output string with the html body
            output = "<html><body>\n"
            daily_users = self.get_daily_users(self.path.split('=', 1)[1])
            # Format output for user
            for line in daily_users.splitlines():
                output += line
                output += "<br />\n"
            output += "\n</body></html>\n"
            self.do_HEAD()
            self.wfile.write(output.encode())
        else:
            # Send error message if GET request does not match either endpoint
            self.send_error(400, "Invalid accept headers", """
            Please enter GET request with one of the three following formats: 
            /collect?cid=<UUID>, /uniques?d=<date>, /uniques?d=<date>&cc=<2 character ISO country code>
            """)

    def handle_collect(self, uuid, country_code):
        """
        Submits the data into the table based on three parameters, the gmt date of the request, the given
        uuid, and the country code of the ip address.  It will send an error message if the given uuid does
        not match the expected format.
        :param uuid: The unique user identification, The uuid is in hexadecimal with format 8-4-4-4-12
        :param country_code: Two character country code of where the user is based out of
        """
        # regex for uuid
        uuid_expression = \
            re.match(r'^[a-fA-f0-9]{8}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{12}$', uuid)
        # if valid uuid
        if uuid_expression:
            # Get current gmt date
            today = 'date' + time.strftime("%Y_%m_%d", time.gmtime())
            database_name = 'UUIDLog.db'
            table_name = "uuid_log"
            # establish connection to sqlite database
            connection = sqlite3.connect(database_name)
            cursor = connection.cursor()
            mutex_lock.acquire()
            # If table does not exist create it, view table details in README
            cursor.execute("CREATE TABLE IF NOT EXISTS %s (uuid CHAR(36) PRIMARY KEY, cc CHAR(2));" % table_name)
            # If row does not exist for the current date, add it to table
            try:
                cursor.execute("ALTER TABLE %s ADD COLUMN '%s' INT DEFAULT 0" % (table_name, today))
            except sqlite3.OperationalError:
                pass
            # if the uuid is not already in the table row into table with valid uuid
            cursor.execute("INSERT OR IGNORE INTO %s (uuid, cc) VALUES (?, ?);" % table_name, [uuid, country_code])
            # Update the current date column for the given uuid to a 1, representing the user did login that day
            cursor.execute("UPDATE %s SET '%s' = 1 WHERE uuid = '%s'" % (table_name, today, uuid))
            mutex_lock.release()
            connection.commit()
            cursor.close()
        else:
            # Send error message if uuid is not valid
            self.send_error(406, "Invalid UUID", "Please submit a UUID with hexadecimals in the "
                                                 "following format 8-4-4-4-12")

    def get_daily_users(self, date):
        """
        Gets the daily users based on the GET request with input of a given date and an optional country code
        :param date: Date submitted by client of format YYYY-MM-DD or YYYY-MM-DD&cc=<cc>
        :return: Output for response body
        """
        # regex to check if user entered date in correct format
        date_expression = re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', date)
        # regex to check if the user entered proper date and country code
        complex_date_expression = re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}&cc=[A-Z]{2}$', date)
        # If proper format continue
        if date_expression or complex_date_expression:
            # Format date to match the database
            formatted_date = "date" + str(date).replace('-', '_')[:10]
            table_name = "uuid_log"
            database_name = 'UUIDLog.db'
            connection = sqlite3.connect(database_name)
            try:
                # If user is just requesting the uuid for a given date, then output the formatted query
                if date_expression:
                    output = pandas.read_sql_query(("SELECT uuid FROM %s WHERE %s = 1;"
                                                    % (table_name, formatted_date)), connection)
                # If user is requesting the uuid's for a given date and country code, then output the formatted query
                else:
                    country_code = date[-2:]
                    output = pandas.read_sql_query(("SELECT uuid FROM %s WHERE (%s = 1 AND cc = '%s');"
                                                    % (table_name, formatted_date, country_code)), connection)
            # If no results or other database error, output: No results found
            except sql.DatabaseError:
                output = "No results found"
            connection.close()
            return str(output)
        else:
            # Send error message if date/country code format is not valid
            self.send_error(406, "Invalid date", "Please submit a date in format YYYY-MM-DD")
            return ""


def run(host='127.0.0.1', port=8080):
    # Create threaded server based on given host and port
    try:
        httpd = ThreadingHTTPServer((host, port), Server)
    except socket.gaierror:
        print("Please list the proper ip address and an unused port")
        exit(1)
    print("Server started http://%s/%s" % (host, port))
    # serve until keyboard interrupt
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped")


if __name__ == '__main__':
    ip = input("Please enter the IP address to host the server: ")
    port = input("Please give the port the service should bind to: ")
    run(ip, int(port))

