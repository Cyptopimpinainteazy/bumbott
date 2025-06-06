import unittest

import hummingbot.connector.exchange.biTrue.biTrue_constants as CONSTANTS
from hummingbot.connector.exchange.biTrue import biTrue_web_utils as web_utils


class BiTrueUtilTestCases(unittest.TestCase):

    def test_public_rest_url(self):
        path_url = "/TEST_PATH"
        domain = "com"
        expected_url = CONSTANTS.REST_URL.format(domain) + CONSTANTS.API_VERSION + path_url
        self.assertEqual(expected_url, web_utils.public_rest_url(path_url, domain))

    def test_private_rest_url(self):
        path_url = "/TEST_PATH"
        domain = "com"
        expected_url = CONSTANTS.REST_URL.format(domain) + CONSTANTS.API_VERSION + path_url
        self.assertEqual(expected_url, web_utils.private_rest_url(path_url, domain))
