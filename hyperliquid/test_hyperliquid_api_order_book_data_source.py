import asyncio
import json
import re
from decimal import Decimal
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

from aioresponses import aioresponses
from bidict import bidict

import hummingbot.connector.exchange.hyperliquid.hyperliquid_web_utils as web_utils
from hummingbot.client.config.client_config_map import ClientConfigMap
from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.exchange.hyperliquid import hyperliquid_constants as CONSTANTS
from hummingbot.connector.exchange.hyperliquid.hyperliquid_api_order_book_data_source import (
    HyperliquidAPIOrderBookDataSource,
)
from hummingbot.connector.exchange.hyperliquid.hyperliquid_exchange import HyperliquidExchange
from hummingbot.connector.test_support.network_mocking_assistant import NetworkMockingAssistant
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType


class HyperliquidAPIOrderBookDataSourceTests(IsolatedAsyncioWrapperTestCase):
    # logging.Level required to receive logs from the data source logger
    level = 0

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.base_asset = "COINALPHA"
        cls.quote_asset = "USDC"
        cls.trading_pair = f"{cls.base_asset}-{cls.quote_asset}"
        cls.ex_trading_pair = f"{cls.base_asset}/{cls.quote_asset}"

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.log_records = []
        self.listening_task = None
        self.mocking_assistant = NetworkMockingAssistant(self.local_event_loop)

        client_config_map = ClientConfigAdapter(ClientConfigMap())
        self.connector = HyperliquidExchange(
            client_config_map,
            hyperliquid_api_key="testkey",
            hyperliquid_api_secret="13e56ca9cceebf1f33065c2c5376ab38570a114bc1b003b60d838f92be9d7930",  # noqa: mock
            use_vault=False,
            trading_pairs=[self.trading_pair],
        )
        self.data_source = HyperliquidAPIOrderBookDataSource(
            trading_pairs=[self.trading_pair],
            connector=self.connector,
            api_factory=self.connector._web_assistants_factory,
        )

        self._original_full_order_book_reset_time = self.data_source.FULL_ORDER_BOOK_RESET_DELTA_SECONDS
        self.data_source.FULL_ORDER_BOOK_RESET_DELTA_SECONDS = -1

        self.data_source.logger().setLevel(1)
        self.data_source.logger().addHandler(self)

        self.resume_test_event = asyncio.Event()

        self.connector._set_trading_pair_symbol_map(
            bidict({f"{self.base_asset}-{self.quote_asset}": self.trading_pair}))

    def tearDown(self) -> None:
        self.listening_task and self.listening_task.cancel()
        self.data_source.FULL_ORDER_BOOK_RESET_DELTA_SECONDS = self._original_full_order_book_reset_time
        super().tearDown()

    def handle(self, record):
        self.log_records.append(record)

    def _is_logged(self, log_level: str, message: str) -> bool:
        return any(record.levelname == log_level and record.getMessage() == message
                   for record in self.log_records)

    def _create_exception_and_unlock_test_with_event(self, exception):
        self.resume_test_event.set()
        raise exception

    def resume_test_callback(self, *_, **__):
        self.resume_test_event.set()
        return None

    def get_rest_snapshot_msg(self) -> Dict:
        return {
            "coin": "COINALPHA/USDC", "levels": [
                [{'px': '2080.3', 'sz': '74.6923', 'n': 2}, {'px': '2080.0', 'sz': '162.2829', 'n': 2},
                 {'px': '1825.5', 'sz': '0.0259', 'n': 1}, {'px': '1823.6', 'sz': '0.0259', 'n': 1}],
                [{'px': '2080.5', 'sz': '73.018', 'n': 2}, {'px': '2080.6', 'sz': '74.6799', 'n': 2},
                 {'px': '2118.9', 'sz': '377.495', 'n': 1}, {'px': '2122.1', 'sz': '348.8644', 'n': 1}]],
            "time": 1700687397643
        }

    def get_ws_snapshot_msg(self) -> Dict:
        return {'channel': 'l2Book', 'data': {'coin': 'COINALPHA/USDC', 'time': 1700687397641, 'levels': [
            [{'px': '2080.3', 'sz': '74.6923', 'n': 2}, {'px': '2080.0', 'sz': '162.2829', 'n': 2},
             {'px': '1825.5', 'sz': '0.0259', 'n': 1}, {'px': '1823.6', 'sz': '0.0259', 'n': 1}],
            [{'px': '2080.5', 'sz': '73.018', 'n': 2}, {'px': '2080.6', 'sz': '74.6799', 'n': 2},
             {'px': '2118.9', 'sz': '377.495', 'n': 1}, {'px': '2122.1', 'sz': '348.8644', 'n': 1}]]}}

    def get_ws_diff_msg(self) -> Dict:
        return {'channel': 'l2Book', 'data': {'coin': 'COINALPHA/USDC', 'time': 1700687397642, 'levels': [
            [{'px': '2080.3', 'sz': '74.6923', 'n': 2}, {'px': '2080.0', 'sz': '162.2829', 'n': 2},
             {'px': '1825.5', 'sz': '0.0259', 'n': 1}, {'px': '1823.6', 'sz': '0.0259', 'n': 1}],
            [{'px': '2080.5', 'sz': '73.018', 'n': 2}, {'px': '2080.6', 'sz': '74.6799', 'n': 2},
             {'px': '2118.9', 'sz': '377.495', 'n': 1}, {'px': '2122.1', 'sz': '348.8644', 'n': 1}]]}}

    def get_ws_diff_msg_2(self) -> Dict:
        return {'channel': 'l2Book', 'data': {'coin': 'COINALPHA/USDC', 'time': 1700687397642, 'levels': [
            [{'px': '2080.4', 'sz': '74.6923', 'n': 2}, {'px': '2080.0', 'sz': '162.2829', 'n': 2},
             {'px': '1825.5', 'sz': '0.0259', 'n': 1}, {'px': '1823.6', 'sz': '0.0259', 'n': 1}],
            [{'px': '2080.5', 'sz': '73.018', 'n': 2}, {'px': '2080.6', 'sz': '74.6799', 'n': 2},
             {'px': '2118.9', 'sz': '377.495', 'n': 1}, {'px': '2122.1', 'sz': '348.8644', 'n': 1}]]}}

    def get_trading_rule_rest_msg(self):
        return [
            {
                "tokens": [
                    {
                        "name": self.quote_asset,
                        "szDecimals": 8,
                        "weiDecimals": 8,
                        "index": 0,
                        "tokenId": "0x6d1e7cde53ba9467b783cb7c530ce054",
                        "isCanonical": True,
                        "evmContract": None,
                        "fullName": None
                    },
                    {
                        "name": self.base_asset,
                        "szDecimals": 0,
                        "weiDecimals": 5,
                        "index": 1,
                        "tokenId": "0xc1fb593aeffbeb02f85e0308e9956a90",
                        "isCanonical": True,
                        "evmContract": None,
                        "fullName": None
                    },
                    {
                        "name": "PURR",
                        "szDecimals": 0,
                        "weiDecimals": 5,
                        "index": 2,
                        "tokenId": "0xc1fb593aeffbeb02f85e0308e9956a90",
                        "isCanonical": True,
                        "evmContract": None,
                        "fullName": None
                    }
                ],
                "universe": [
                    {
                        "name": "COINALPHA/USDC",
                        "tokens": [1, 0],
                        "index": 0,
                        "isCanonical": True
                    },
                    {
                        "name": "@1",
                        "tokens": [2, 0],
                        "index": 1,
                        "isCanonical": True
                    }
                ]
            },
            [
                {
                    'prevDayPx': '0.22916',
                    'dayNtlVlm': '4265022.87833',
                    'markPx': '0.22923',
                    'midPx': '0.229235',
                    'circulatingSupply': '598274922.83822',
                    'coin': 'COINALPHA/USDC'
                },
                {
                    'prevDayPx': '25.236',
                    'dayNtlVlm': '315299.16652',
                    'markPx': '25.011',
                    'midPx': '24.9835',
                    'circulatingSupply': '997372.88712882',
                    'coin': '@1'
                }
            ]
        ]

    @aioresponses()
    async def test_get_new_order_book_successful(self, mock_api):
        self._simulate_trading_rules_initialized()
        endpoint = CONSTANTS.SNAPSHOT_REST_URL
        url = web_utils.public_rest_url(endpoint)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?") + ".*")
        resp = self.get_rest_snapshot_msg()
        mock_api.post(regex_url, body=json.dumps(resp))

        order_book = await self.data_source.get_new_order_book(self.trading_pair)

        self.assertEqual(1700687397643, order_book.snapshot_uid)
        bids = list(order_book.bid_entries())
        asks = list(order_book.ask_entries())
        self.assertEqual(4, len(bids))
        self.assertEqual(2080.3, bids[0].price)
        self.assertEqual(74.6923, bids[0].amount)
        self.assertEqual(4, len(asks))
        self.assertEqual(2080.5, asks[0].price)
        self.assertEqual(73.018, asks[0].amount)

    @aioresponses()
    async def test_get_new_order_book_raises_exception(self, mock_api):
        self._simulate_trading_rules_initialized()
        endpoint = CONSTANTS.SNAPSHOT_REST_URL
        url = web_utils.public_rest_url(endpoint)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?") + ".*")

        mock_api.post(regex_url, status=400)
        with self.assertRaises(IOError):
            await self.data_source.get_new_order_book(self.trading_pair)

    @patch("aiohttp.ClientSession.ws_connect", new_callable=AsyncMock)
    async def test_listen_for_subscriptions_subscribes_to_trades_diffs_and_orderbooks(self, ws_connect_mock):
        self._simulate_trading_rules_initialized()
        ws_connect_mock.return_value = self.mocking_assistant.create_websocket_mock()

        result_subscribe_diffs = self.get_ws_snapshot_msg()

        self.mocking_assistant.add_websocket_aiohttp_message(
            websocket_mock=ws_connect_mock.return_value,
            message=json.dumps(result_subscribe_diffs),
        )
        self.listening_task = self.local_event_loop.create_task(self.data_source.listen_for_subscriptions())

        await self.mocking_assistant.run_until_all_aiohttp_messages_delivered(ws_connect_mock.return_value)

        sent_subscription_messages = self.mocking_assistant.json_messages_sent_through_websocket(
            websocket_mock=ws_connect_mock.return_value
        )

        self.assertEqual(2, len(sent_subscription_messages))
        expected_trade_subscription_channel = CONSTANTS.TRADES_ENDPOINT_NAME
        expected_trade_subscription_payload = self.connector.name_to_coin[self.trading_pair.replace("-", "/")]
        self.assertEqual(expected_trade_subscription_channel, sent_subscription_messages[0]["subscription"]["type"])
        self.assertEqual(expected_trade_subscription_payload, sent_subscription_messages[0]["subscription"]["coin"])
        expected_depth_subscription_channel = CONSTANTS.DEPTH_ENDPOINT_NAME
        expected_depth_subscription_payload = self.connector.name_to_coin[self.trading_pair.replace("-", "/")]
        self.assertEqual(expected_depth_subscription_channel, sent_subscription_messages[1]["subscription"]["type"])
        self.assertEqual(expected_depth_subscription_payload, sent_subscription_messages[1]["subscription"]["coin"])

        self.assertTrue(
            self._is_logged("INFO", "Subscribed to public order book, trade channels...")
        )

    @patch("hummingbot.core.data_type.order_book_tracker_data_source.OrderBookTrackerDataSource._sleep")
    @patch("aiohttp.ClientSession.ws_connect")
    async def test_listen_for_subscriptions_raises_cancel_exception(self, mock_ws, _: AsyncMock):
        mock_ws.side_effect = asyncio.CancelledError

        with self.assertRaises(asyncio.CancelledError):
            await self.data_source.listen_for_subscriptions()

    @patch("hummingbot.core.data_type.order_book_tracker_data_source.OrderBookTrackerDataSource._sleep")
    @patch("aiohttp.ClientSession.ws_connect", new_callable=AsyncMock)
    async def test_listen_for_subscriptions_logs_exception_details(self, mock_ws, sleep_mock):
        mock_ws.side_effect = Exception("TEST ERROR.")
        sleep_mock.side_effect = lambda _: self._create_exception_and_unlock_test_with_event(asyncio.CancelledError())

        self.listening_task = self.local_event_loop.create_task(self.data_source.listen_for_subscriptions())

        await self.resume_test_event.wait()

        self.assertTrue(
            self._is_logged(
                "ERROR",
                "Unexpected error occurred when listening to order book streams. Retrying in 5 seconds..."
            )
        )

    async def test_subscribe_to_channels_raises_cancel_exception(self):
        self._simulate_trading_rules_initialized()
        mock_ws = MagicMock()
        mock_ws.send.side_effect = asyncio.CancelledError

        with self.assertRaises(asyncio.CancelledError):
            await self.data_source._subscribe_channels(mock_ws)

    async def test_subscribe_to_channels_raises_exception_and_logs_error(self):
        mock_ws = MagicMock()
        mock_ws.send.side_effect = Exception("Test Error")

        with self.assertRaises(Exception):
            await self.data_source._subscribe_channels(mock_ws)

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error occurred subscribing to order book data streams.")
        )

    async def test_listen_for_trades_cancelled_when_listening(self):
        mock_queue = MagicMock()
        mock_queue.get.side_effect = asyncio.CancelledError()
        self.data_source._message_queue[self.data_source._trade_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        with self.assertRaises(asyncio.CancelledError):
            await self.data_source.listen_for_trades(self.local_event_loop, msg_queue)

    def _simulate_trading_rules_initialized(self):
        mocked_response = self.get_trading_rule_rest_msg()
        self.connector._initialize_trading_pair_symbols_from_exchange_info(mocked_response)
        self.connector.coin_to_asset = {asset_info["name"]: asset for (asset, asset_info) in
                                        enumerate(mocked_response[0]["tokens"])}
        self.connector.name_to_coin = {asset_info["name"]: asset_info["name"] for asset_info in
                                       mocked_response[0]["universe"]}
        self.connector._trading_rules = {
            self.trading_pair: TradingRule(
                trading_pair=self.trading_pair,
                min_order_size=Decimal(str(0.01)),
                min_price_increment=Decimal(str(0.0001)),
                min_base_amount_increment=Decimal(str(0.000001)),
            )
        }

    async def test_listen_for_trades_logs_exception(self):
        incomplete_resp = {
            "code": 0,
            "message": "",
            "data": [
                {
                    "created_at": 1642994704633,
                    "trade_id": 1005483402,
                    "instrument_id": "COINALPHA-USDC",
                    "qty": "1.00000000",
                    "side": "sell",
                    "sigma": "0.00000000",
                    "index_price": "2447.79750000",
                    "underlying_price": "0.00000000",
                    "is_block_trade": False
                },
                {
                    "created_at": 1642994704241,
                    "trade_id": 1005483400,
                    "instrument_id": "COINALPHA-USDC",
                    "qty": "1.00000000",
                    "side": "sell",
                    "sigma": "0.00000000",
                    "index_price": "2447.79750000",
                    "underlying_price": "0.00000000",
                    "is_block_trade": False
                }
            ]
        }

        mock_queue = AsyncMock()
        mock_queue.get.side_effect = [incomplete_resp, asyncio.CancelledError()]
        self.data_source._message_queue[self.data_source._trade_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        try:
            await self.data_source.listen_for_trades(self.local_event_loop, msg_queue)
        except asyncio.CancelledError:
            pass

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error when processing public trade updates from exchange"))

    async def test_listen_for_trades_successful(self):
        self._simulate_trading_rules_initialized()
        mock_queue = AsyncMock()
        trade_event = {'channel': 'trades', 'data': [
            {'coin': 'COINALPHA/USDC', 'side': 'A', 'px': '2009.0', 'sz': '0.0079', 'time': 1701156061468,
             'hash': '0x3e2bc327cc925903cebe0408315a98010b002fda921d23fd1468bbb5d573f902'}]}  # noqa: mock

        mock_queue.get.side_effect = [trade_event, asyncio.CancelledError()]
        self.data_source._message_queue[self.data_source._trade_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        self.listening_task = self.local_event_loop.create_task(
            self.data_source.listen_for_trades(self.local_event_loop, msg_queue))

        msg: OrderBookMessage = await msg_queue.get()

        self.assertEqual(OrderBookMessageType.TRADE, msg.type)
        self.assertEqual(trade_event["data"][0]["hash"], msg.trade_id)
        self.assertEqual(trade_event["data"][0]["time"] * 1e-3, msg.timestamp)

    async def test_listen_for_order_book_diffs_cancelled(self):
        mock_queue = AsyncMock()
        mock_queue.get.side_effect = asyncio.CancelledError()
        self.data_source._message_queue[self.data_source._diff_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        with self.assertRaises(asyncio.CancelledError):
            await self.data_source.listen_for_order_book_diffs(self.local_event_loop, msg_queue)

    async def test_listen_for_order_book_diffs_logs_exception(self):
        self._simulate_trading_rules_initialized()
        incomplete_resp = self.get_ws_diff_msg()
        del incomplete_resp["data"]["time"]

        mock_queue = AsyncMock()
        mock_queue.get.side_effect = [incomplete_resp, asyncio.CancelledError()]
        self.data_source._message_queue[self.data_source._diff_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        try:
            await self.data_source.listen_for_order_book_diffs(self.local_event_loop, msg_queue)
        except asyncio.CancelledError:
            pass

        self.assertTrue(
            self._is_logged("ERROR", "Unexpected error when processing public order book updates from exchange"))

    async def test_listen_for_order_book_diffs_successful(self):
        self._simulate_trading_rules_initialized()
        mock_queue = AsyncMock()
        diff_event = self.get_ws_diff_msg_2()
        mock_queue.get.side_effect = [diff_event, asyncio.CancelledError()]
        self.data_source._message_queue[self.data_source._diff_messages_queue_key] = mock_queue

        msg_queue: asyncio.Queue = asyncio.Queue()

        self.listening_task = self.local_event_loop.create_task(
            self.data_source.listen_for_order_book_diffs(self.local_event_loop, msg_queue))

        msg: OrderBookMessage = await msg_queue.get()

        self.assertEqual(OrderBookMessageType.DIFF, msg.type)
        self.assertEqual(-1, msg.trade_id)
        expected_update_id = diff_event["data"]["time"]
        self.assertEqual(expected_update_id, msg.update_id)

        bids = msg.bids
        asks = msg.asks
        self.assertEqual(4, len(bids))
        self.assertEqual(2080.4, bids[0].price)
        self.assertEqual(74.6923, bids[0].amount)
        self.assertEqual(4, len(asks))
        self.assertEqual(2080.5, asks[0].price)
        self.assertEqual(73.018, asks[0].amount)

    @aioresponses()
    async def test_listen_for_order_book_snapshots_cancelled_when_fetching_snapshot(self, mock_api):
        self._simulate_trading_rules_initialized()
        endpoint = CONSTANTS.SNAPSHOT_REST_URL
        url = web_utils.public_rest_url(endpoint)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?") + ".*")

        mock_api.post(regex_url, exception=asyncio.CancelledError)

        with self.assertRaises(asyncio.CancelledError):
            await self.data_source.listen_for_order_book_snapshots(self.local_event_loop, asyncio.Queue())

    @aioresponses()
    @patch("hummingbot.core.data_type.order_book_tracker_data_source.OrderBookTrackerDataSource._sleep")
    async def test_listen_for_order_book_snapshots_log_exception(self, mock_api, sleep_mock):
        msg_queue: asyncio.Queue = asyncio.Queue()
        sleep_mock.side_effect = lambda _: self._create_exception_and_unlock_test_with_event(asyncio.CancelledError())

        endpoint = CONSTANTS.SNAPSHOT_REST_URL
        url = web_utils.public_rest_url(endpoint)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?") + ".*")

        mock_api.post(regex_url, exception=Exception)

        self.listening_task = self.local_event_loop.create_task(
            self.data_source.listen_for_order_book_snapshots(self.local_event_loop, msg_queue)
        )
        await self.resume_test_event.wait()

        self.assertTrue(
            self._is_logged("ERROR", f"Unexpected error fetching order book snapshot for {self.trading_pair}.")
        )

    @aioresponses()
    async def test_listen_for_order_book_snapshots_successful(self, mock_api):
        self._simulate_trading_rules_initialized()
        msg_queue: asyncio.Queue = asyncio.Queue()
        endpoint = CONSTANTS.SNAPSHOT_REST_URL
        url = web_utils.public_rest_url(endpoint)
        regex_url = re.compile(f"^{url}".replace(".", r"\.").replace("?", r"\?") + ".*")

        resp = self.get_rest_snapshot_msg()

        mock_api.post(regex_url, body=json.dumps(resp))

        self.listening_task = self.local_event_loop.create_task(
            self.data_source.listen_for_order_book_snapshots(self.local_event_loop, msg_queue)
        )

        msg: OrderBookMessage = await msg_queue.get()

        self.assertEqual(OrderBookMessageType.SNAPSHOT, msg.type)
        self.assertEqual(-1, msg.trade_id)
        expected_update_id = resp["time"]
        self.assertEqual(expected_update_id, msg.update_id)

        bids = msg.bids
        asks = msg.asks

        self.assertEqual(4, len(bids))
        self.assertEqual(2080.3, bids[0].price)
        self.assertEqual(74.6923, bids[0].amount)
        self.assertEqual(4, len(asks))
        self.assertEqual(2080.5, asks[0].price)
        self.assertEqual(73.018, asks[0].amount)
