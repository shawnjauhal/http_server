import unittest
import requests
import re
import urllib.request

"""
Author: Shawn Jauhal
Date: November 1st, 2020
Class: TestServer

Preforms basic tests for class: Server
Google Cloud Platform test platform ip:port:  35.215.7.18:8080
"""

ip = '35.215.7.18'
port = '8080'

proper_uuid = "123e4567-e89b-12d3-a456-426614174000"
improper_uuid = "123e4567e89b12d3a456426614174000"

proper_date = "2020-10-25"
improper_date = "10-25-2020"
not_found_date = "2020-10-04"

proper_country_code = 'US'
improper_country_code = 'USA'


class TestServer(unittest.TestCase):

    def test_proper_collect(self):
        """
        Tests the collect endpoint with a properly formatted uuid
        :assert True: If server sends status code 200
        """
        response = requests.get("http://%s:%s/collect?cid=%s" % (ip, port, proper_uuid))
        if response.status_code == 200:
            assert True
        else:
            assert False

    def test_improper_collect(self):
        """
        Tests errors on the collect endpoint by calling a uuid without proper format
        :assert True: If server sends status code 406
        """
        response = requests.get("http://%s:%s/collect?cid=%s" % (ip, port, improper_uuid))
        if response.status_code == 406:
            assert True
        else:
            assert False

    def test_simple_date(self):
        """
        Tests the uniques endpoint to see if the proper amount of uuid's are sent given a date with a known amount of
        matching uuid's
        :assert True: If the correct number of uuid's are received, in this case 13
        """
        url = "http://%s:%s/uniques?d=%s" % (ip, port, proper_date)
        response = requests.get(url)
        url_p = urllib.request.urlopen(url)
        bytes = url_p.read()
        html = bytes.decode("utf-8")
        count_entries = 0
        for line in html.splitlines():
            is_uuid = re.search(r'[a-fA-f0-9]{8}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{12}', line)
            if is_uuid:
                count_entries += 1
        if count_entries == 13:
            assert True
        else:
            assert False

    def test_improper_date(self):
        """
        Tests the uniques endpoint with an improperly formatted date expecting an error
        :assert True: If server sends status code 406
        """
        url = "http://%s:%s/uniques?d=%s" % (ip, port, improper_date)
        response = requests.get(url)
        if response.status_code == 406:
            assert True
        else:
            assert False

    def test_no_data_found(self):
        """
        Tests the uniques endpoint with a properly formatted date, but one where the database has no data for
        :assert True: if html response contains 'No results found'
        """
        url = "http://%s:%s/uniques?d=%s" % (ip, port, not_found_date)
        response = requests.get(url)
        url_p = urllib.request.urlopen(url)
        bytes = url_p.read()
        html = bytes.decode("utf-8")
        if "No results found" in html and response.status_code == 200:
            assert True
        else:
            assert False

    def test_date_country_code(self):
        """
        Tests the uniques endpoint to see if the proper amount of uuid's are sent given a date and country code with a
        known amount of matching uuid's
        :assert True: If the correct number of uuid's are received, in this case 4
        """
        url = "http://%s:%s/uniques?d=%s&cc=%s" % (ip, port, proper_date, proper_country_code)
        response = requests.get(url)
        url_p = urllib.request.urlopen(url)
        bytes = url_p.read()
        html = bytes.decode("utf-8")
        count_entries = 0
        for line in html.splitlines():
            is_uuid = re.search(r'[a-fA-f0-9]{8}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{4}-[a-fA-f0-9]{12}', line)
            if is_uuid:
                count_entries += 1
        if count_entries == 4:
            assert True
        else:
            assert False

    def test_improper_date_country_code(self):
        """
        Tests the uniques endpoint with an properly formatted date and improperly formatted country code
        expecting an error
        :assert True: If server sends status code 406
        """
        url = "http://%s:%s/uniques?d=%s&cc=%s" % (ip, port, proper_date, improper_country_code)
        response = requests.get(url)
        if response.status_code == 406:
            assert True
        else:
            assert False


if __name__ == '__main__':
    unittest.main()