# -*- coding: utf-8 -*-

"""
unit tests for hummingbot.core.utils.estimate_fee
"""

import unittest
from decimal import Decimal

from hummingbot.core.data_type.trade_fee import AddedToCostTradeFee, DeductedFromReturnsTradeFee
from hummingbot.core.utils.estimate_fee import estimate_fee


class EstimateFeeTest(unittest.TestCase):

    def test_estimate_fee(self):
        """
        test the estimate_fee function
        """

        # test against centralized exchanges
        self.assertEqual(estimate_fee("kucoin", True), AddedToCostTradeFee(percent=Decimal('0.001'), flat_fees=[]))
        self.assertEqual(estimate_fee("kucoin", False), AddedToCostTradeFee(percent=Decimal('0.001'), flat_fees=[]))
        self.assertEqual(estimate_fee("binance", True), DeductedFromReturnsTradeFee(percent=Decimal('0.001'), flat_fees=[]))
        self.assertEqual(estimate_fee("binance", False), DeductedFromReturnsTradeFee(percent=Decimal('0.001'), flat_fees=[]))

        # test against exchanges that do not exist in hummingbot.client.settings.CONNECTOR_SETTINGS
        self.assertRaisesRegex(Exception, "^Invalid connector", estimate_fee, "does_not_exist", True)
        self.assertRaisesRegex(Exception, "Invalid connector", estimate_fee, "does_not_exist", False)
