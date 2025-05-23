import json
from decimal import Decimal
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase

from aioresponses import aioresponses

from hummingbot.connector.exchange.ascend_ex import ascend_ex_constants as CONSTANTS
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.rate_oracle.sources.ascend_ex_rate_source import AscendExRateSource


class AscendExRateSourceTest(IsolatedAsyncioWrapperTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.target_token = "COINALPHA"
        cls.global_token = "HBOT"
        cls.trading_pair = combine_to_hb_trading_pair(base=cls.target_token, quote=cls.global_token)
        cls.ignored_trading_pair = combine_to_hb_trading_pair(base="SOME", quote="PAIR")

    def setup_ascend_ex_responses(self, mock_api, expected_rate: Decimal):
        symbols_url = f"{CONSTANTS.PUBLIC_REST_URL}{CONSTANTS.PRODUCTS_PATH_URL}"
        symbols_response = {  # truncated response
            "code": 0,
            "data": [
                {
                    "symbol": f"{self.target_token}/{self.global_token}",
                    "baseAsset": self.target_token,
                    "quoteAsset": self.global_token,
                    "statusCode": "Normal",
                },
                {"symbol": "SOME/PAIR", "baseAsset": "SOME", "quoteAsset": "PAIR", "statusCode": "Normal"},
            ],
        }
        mock_api.get(url=symbols_url, body=json.dumps(symbols_response))
        prices_url = f"{CONSTANTS.PUBLIC_REST_URL}{CONSTANTS.TICKER_PATH_URL}"
        prices_response = {  # truncated response
            "code": 0,
            "data": [
                {
                    "symbol": f"{self.target_token}/{self.global_token}",
                    "ask": [str(expected_rate + Decimal("0.1")), "43641"],
                    "bid": [str(expected_rate - Decimal("0.1")), "443"],
                }
            ],
        }
        mock_api.get(url=prices_url, body=json.dumps(prices_response))

    @aioresponses()
    async def test_get_prices(self, mock_api):
        expected_rate = Decimal("10")
        self.setup_ascend_ex_responses(mock_api=mock_api, expected_rate=expected_rate)

        rate_source = AscendExRateSource()
        prices = await rate_source.get_prices()

        self.assertIn(self.trading_pair, prices)
        self.assertEqual(expected_rate, prices[self.trading_pair])
        self.assertNotIn(self.ignored_trading_pair, prices)
