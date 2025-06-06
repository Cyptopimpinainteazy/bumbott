import asyncio
import time
import unittest
from decimal import Decimal
from typing import Awaitable
from unittest.mock import patch

from hummingbot.core.data_type.common import OrderType, PositionAction, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.limit_order import LimitOrder
from hummingbot.core.data_type.trade_fee import AddedToCostTradeFee, TokenAmount
from hummingbot.core.rate_oracle.rate_oracle import RateOracle


class InFlightOrderPyUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.ev_loop = asyncio.get_event_loop()

        cls.base_asset = "COINALPHA"
        cls.quote_asset = "HBOT"
        cls.trading_pair = f"{cls.base_asset}-{cls.quote_asset}"

        cls.client_order_id = "someClientOrderId"
        cls.exchange_order_id = "someExchangeOrderId"
        cls.trade_fee_percent = Decimal("0.01")

    def async_run_with_timeout(self, coroutine: Awaitable, timeout: int = 1):
        ret = self.ev_loop.run_until_complete(asyncio.wait_for(coroutine, timeout))
        return ret

    def async_run_with_timeout_coroutine_must_raise_timeout(self, coroutine: Awaitable, timeout: float = 1):
        class DesiredError(Exception):
            pass

        async def run_coro_that_raises(coro: Awaitable):
            try:
                await coro
            except asyncio.TimeoutError:
                raise DesiredError

        try:
            self.async_run_with_timeout(run_coro_that_raises(coroutine), timeout)
        except DesiredError:  # the coroutine raised an asyncio.TimeoutError as expected
            raise asyncio.TimeoutError
        except asyncio.TimeoutError:  # the coroutine did not finish on time
            raise RuntimeError

    def _simulate_order_created(self, order: InFlightOrder):
        order.current_state = OrderState.OPEN
        order.update_exchange_order_id(self.exchange_order_id)

    def _simulate_cancel_order_request_sent(self, order: InFlightOrder):
        order.current_state = OrderState.PENDING_CANCEL

    def _simulate_order_cancelled(self, order: InFlightOrder):
        order.current_state = OrderState.CANCELED

    def _simulate_order_failed(self, order: InFlightOrder):
        order.current_state = OrderState.FAILED

    def _simulate_order_partially_filled(self, order: InFlightOrder):
        order.current_state = OrderState.PARTIALLY_FILLED
        order.executed_amount_base = order.amount / Decimal("2")

    def _simulate_order_completely_filled(self, order: InFlightOrder):
        order.current_state = OrderState.FILLED
        order.executed_amount_base = order.amount

    def test_in_flight_order_states(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        self.assertTrue(order.is_open)
        self.assertIsNone(order.exchange_order_id)
        self.assertFalse(order.exchange_order_id_update_event.is_set())

        # Simulate Order Created
        self._simulate_order_created(order)

        self.assertTrue(order.is_open)
        self.assertIsNotNone(order.exchange_order_id)
        self.assertTrue(order.exchange_order_id_update_event.is_set())

        # Simulate Order Cancellation request sent
        self._simulate_cancel_order_request_sent(order)

        self.assertTrue(order.is_pending_cancel_confirmation
                        and order.is_open
                        and not order.is_cancelled
                        and not order.is_done)

        # Simulate Order Cancelled
        self._simulate_order_cancelled(order)

        self.assertTrue(order.is_done and order.is_cancelled)

        failed_order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        # Simulate Order Failed
        self._simulate_order_failed(failed_order)

        self.assertTrue(failed_order.is_failure and failed_order.is_done)

        filled_order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        # Simulate Order Partially Filled
        self._simulate_order_partially_filled(filled_order)

        self.assertTrue(filled_order.is_open and not filled_order.is_done)

        # Simulate Order Completely Filled
        self._simulate_order_completely_filled(filled_order)

        self.assertTrue(filled_order.is_done and filled_order.is_filled)

    def test_average_executed_price(self):
        order_0: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        self.assertIsNone(order_0.average_executed_price)

        trade_update_0: TradeUpdate = TradeUpdate(
            trade_id="someTradeId",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=order_0.trading_pair,
            fill_price=order_0.price,
            fill_base_amount=order_0.amount,
            fill_quote_amount=(order_0.price * order_0.amount),
            fee=AddedToCostTradeFee(flat_fees=[TokenAmount(self.base_asset, Decimal(0.01) * order_0.amount)]),
            fill_timestamp=time.time(),
        )
        # Order completely filled after single trade update
        order_0.order_fills.update({trade_update_0.trade_id: trade_update_0})

        self.assertEqual(order_0.price, order_0.average_executed_price)

        order_1: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        trade_update_1: TradeUpdate = TradeUpdate(
            trade_id="someTradeId_1",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=order_1.trading_pair,
            fill_price=Decimal("0.5"),
            fill_base_amount=(order_1.amount / Decimal("2.0")),
            fill_quote_amount=(order_1.price * (order_1.amount / Decimal("2.0"))),
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(self.base_asset, Decimal(0.01) * (order_1.amount / Decimal("2.0")))]),
            fill_timestamp=time.time(),
        )

        trade_update_2: TradeUpdate = TradeUpdate(
            trade_id="someTradeId_2",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=order_1.trading_pair,
            fill_price=order_1.price,
            fill_base_amount=(order_1.amount / Decimal("2.0")),
            fill_quote_amount=(order_1.price * (order_1.amount / Decimal("2.0"))),
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(self.base_asset, Decimal(0.01) * (order_1.amount / Decimal("2.0")))]),
            fill_timestamp=time.time(),
        )

        # Order completely filled after 2 trade updates
        order_1.order_fills.update(
            {
                trade_update_1.trade_id: trade_update_1,
                trade_update_2.trade_id: trade_update_2,
            }
        )
        expected_average_price = (
            sum([order_fill.fill_price * order_fill.fill_base_amount for order_fill in order_1.order_fills.values()])
            / order_1.amount
        )
        self.assertEqual(expected_average_price, order_1.average_executed_price)

    @patch("hummingbot.core.data_type.in_flight_order.GET_EX_ORDER_ID_TIMEOUT", 0.1)
    def test_get_exchange_order_id(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )
        self.assertIsNone(order.exchange_order_id)
        self.assertFalse(order.exchange_order_id_update_event.is_set())
        with self.assertRaises(asyncio.TimeoutError):
            self.async_run_with_timeout_coroutine_must_raise_timeout(order.get_exchange_order_id())

        order.update_exchange_order_id(self.exchange_order_id)
        result = self.async_run_with_timeout(order.get_exchange_order_id())

        self.assertEqual(self.exchange_order_id, result)
        self.assertTrue(order.exchange_order_id_update_event.is_set())

    def test_from_json(self):
        fee = AddedToCostTradeFee(
            percent=Decimal("0.5"),
            percent_token=self.quote_asset
        )
        trade_update = TradeUpdate(
            trade_id="12345",
            client_order_id=self.client_order_id,
            exchange_order_id="EOID1",
            trading_pair=self.trading_pair,
            fill_timestamp=1640001112,
            fill_price=Decimal("1000.11"),
            fill_base_amount=Decimal("2"),
            fill_quote_amount=Decimal("2000.22"),
            fee=fee,
        )

        order_json = {
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "trading_pair": self.trading_pair,
            "order_type": OrderType.LIMIT.name,
            "trade_type": TradeType.BUY.name,
            "price": "1.0",
            "amount": "1000.0",
            "executed_amount_base": "0",
            "executed_amount_quote": "0",
            "fee_asset": None,
            "fee_paid": "0",
            "last_state": "0",
            "leverage": "1",
            "position": "NIL",
            "creation_timestamp": 1640001112.0,
            "last_update_timestamp": 1640001113.0,
            "order_fills": {"1": trade_update.to_json()}
        }

        expected_order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )
        expected_order.last_update_timestamp = 1640001113.0

        order_from_json = InFlightOrder.from_json(order_json)
        self.assertEqual(expected_order, order_from_json)
        self.assertFalse(order_from_json.completely_filled_event.is_set())

        self.assertIn("1", order_from_json.order_fills)
        self.assertEqual(trade_update, order_from_json.order_fills["1"])
        self.assertEqual(1640001113.0, order_from_json.last_update_timestamp)

    def test_from_json_does_not_fail_when_order_fills_not_present(self):
        order_json = {
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "trading_pair": self.trading_pair,
            "order_type": OrderType.LIMIT.name,
            "trade_type": TradeType.BUY.name,
            "price": "1.0",
            "amount": "1000.0",
            "executed_amount_base": "0",
            "executed_amount_quote": "0",
            "fee_asset": None,
            "fee_paid": "0",
            "last_state": "0",
            "leverage": "1",
            "position": PositionAction.NIL.value,
            "creation_timestamp": 1640001112
        }

        expected_order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        order_from_json = InFlightOrder.from_json(order_json)
        self.assertEqual(expected_order, order_from_json)
        self.assertFalse(order_from_json.completely_filled_event.is_set())

    def test_completed_order_recovered_from_json_has_completed_event_updated(self):
        order_json = {
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "trading_pair": self.trading_pair,
            "order_type": OrderType.LIMIT.name,
            "trade_type": TradeType.BUY.name,
            "price": "1.0",
            "amount": "1000.0",
            "executed_amount_base": "1000.0",
            "executed_amount_quote": "1100.0",
            "fee_asset": None,
            "fee_paid": "0",
            "last_state": "0",
            "leverage": "1",
            "position": "NIL",
            "creation_timestamp": 1640001112.0,
        }

        expected_order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )
        expected_order.executed_amount_base = Decimal("1000")
        expected_order.executed_amount_quote = Decimal("1100")

        order_from_json = InFlightOrder.from_json(order_json)
        self.assertEqual(expected_order, order_from_json)
        self.assertTrue(order_from_json.completely_filled_event.is_set())

    @patch.object(RateOracle, "get_pair_rate")
    def test_to_json(self, mock_get_pair_rate):
        mock_get_pair_rate.return_value = Decimal("1.0")
        fee = AddedToCostTradeFee(
            percent=Decimal("0.5"),
            percent_token=self.quote_asset
        )
        trade_update = TradeUpdate(
            trade_id="12345",
            client_order_id=self.client_order_id,
            exchange_order_id="EOID1",
            trading_pair=self.trading_pair,
            fill_timestamp=1640001112,
            fill_price=Decimal("1000.11"),
            fill_base_amount=Decimal("2"),
            fill_quote_amount=Decimal("2000.22"),
            fee=fee,
        )

        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )
        order.order_fills["1"] = trade_update

        order_json = order.to_json()

        self.assertIsInstance(order_json, dict)

        self.assertEqual(order_json["client_order_id"], order.client_order_id)
        self.assertEqual(order_json["exchange_order_id"], order.exchange_order_id)
        self.assertEqual(order_json["trading_pair"], order.trading_pair)
        self.assertEqual(order_json["order_type"], order.order_type.name)
        self.assertEqual(order_json["trade_type"], order.trade_type.name)
        self.assertEqual(order_json["price"], str(order.price))
        self.assertEqual(order_json["amount"], str(order.amount))
        self.assertEqual(order_json["executed_amount_base"], str(order.executed_amount_base))
        self.assertEqual(order_json["executed_amount_quote"], str(order.executed_amount_quote))
        self.assertEqual(order_json["last_state"], str(order.current_state.value))
        self.assertEqual(order_json["leverage"], str(order.leverage))
        self.assertEqual(order_json["position"], order.position.value)
        self.assertEqual(order_json["creation_timestamp"], order.creation_timestamp)
        self.assertEqual(order_json["last_update_timestamp"], order.last_update_timestamp)
        self.assertEqual(order_json["order_fills"], {"1": trade_update.to_json()})

    def test_to_limit_order(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.223334,
            price=Decimal("1.0"),
        )

        expected_limit_order: LimitOrder = LimitOrder(
            client_order_id=order.client_order_id,
            trading_pair=order.trading_pair,
            is_buy=True,
            base_currency=self.base_asset,
            quote_currency=self.quote_asset,
            price=Decimal("1.0"),
            quantity=Decimal("1000.0"),
            filled_quantity=Decimal("0"),
            creation_timestamp=1640001112223334
        )

        limit_order = order.to_limit_order()

        self.assertIsInstance(limit_order, LimitOrder)

        self.assertEqual(limit_order.client_order_id, expected_limit_order.client_order_id)
        self.assertEqual(limit_order.trading_pair, expected_limit_order.trading_pair)
        self.assertEqual(limit_order.is_buy, expected_limit_order.is_buy)
        self.assertEqual(limit_order.base_currency, expected_limit_order.base_currency)
        self.assertEqual(limit_order.quote_currency, expected_limit_order.quote_currency)
        self.assertEqual(limit_order.price, expected_limit_order.price)
        self.assertEqual(limit_order.quantity, expected_limit_order.quantity)
        self.assertEqual(limit_order.filled_quantity, expected_limit_order.filled_quantity)
        self.assertEqual(limit_order.creation_timestamp, expected_limit_order.creation_timestamp)
        self.assertEqual(limit_order.status, expected_limit_order.status)

    def test_update_with_order_update_client_order_id_mismatch(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        mismatch_order_update: OrderUpdate = OrderUpdate(
            client_order_id="mismatchClientOrderId",
            exchange_order_id="mismatchExchangeOrderId",
            trading_pair=self.trading_pair,
            update_timestamp=1,
            new_state=OrderState.OPEN,
        )

        self.assertFalse(order.update_with_order_update(mismatch_order_update))
        self.assertEqual(Decimal("0"), order.executed_amount_base)
        self.assertEqual(Decimal("0"), order.executed_amount_quote)
        self.assertEqual(order.creation_timestamp, order.last_update_timestamp)

    def test_update_with_order_update_open_order(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        open_order_update: OrderUpdate = OrderUpdate(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            update_timestamp=1,
            new_state=OrderState.OPEN,
        )

        self.assertTrue(order.update_with_order_update(open_order_update))
        self.assertEqual(Decimal("0"), order.executed_amount_base)
        self.assertEqual(Decimal("0"), order.executed_amount_quote)
        self.assertEqual(1, order.last_update_timestamp)

    def test_update_with_order_update_multiple_order_updates(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        order_update_1: OrderUpdate = OrderUpdate(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            update_timestamp=1,
            new_state=OrderState.PARTIALLY_FILLED,
        )

        self.assertTrue(order.update_with_order_update(order_update_1))
        # Order updates should not modify executed values
        self.assertEqual(Decimal(0), order.executed_amount_base)
        self.assertEqual(Decimal(0), order.executed_amount_quote)
        self.assertEqual(order.last_update_timestamp, 1)
        self.assertEqual(0, len(order.order_fills))
        self.assertTrue(order.is_open)

        order_update_2: OrderUpdate = OrderUpdate(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            update_timestamp=2,
            new_state=OrderState.FILLED,
        )

        self.assertTrue(order.update_with_order_update(order_update_2))
        # Order updates should not modify executed values
        self.assertEqual(Decimal(0), order.executed_amount_base)
        self.assertEqual(Decimal(0), order.executed_amount_quote)
        self.assertEqual(order.last_update_timestamp, 2)
        self.assertEqual(0, len(order.order_fills))
        self.assertTrue(order.is_done)

    def test_update_exchange_id_with_order_update(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        order_update: OrderUpdate = OrderUpdate(
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            update_timestamp=1,
            new_state=OrderState.OPEN,
        )

        result = order.update_with_order_update(order_update)
        self.assertTrue(result)
        self.assertEqual(self.exchange_order_id, order.exchange_order_id)
        self.assertTrue(order.exchange_order_id_update_event.is_set())
        self.assertEqual(0, len(order.order_fills))

    def test_update_with_trade_update_trade_update_with_trade_fee_percent(self):

        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        trade_update: TradeUpdate = TradeUpdate(
            trade_id="someTradeId",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            fill_price=Decimal("1.0"),
            fill_base_amount=Decimal("500.0"),
            fill_quote_amount=Decimal("500.0"),
            fee=AddedToCostTradeFee(percent=self.trade_fee_percent, percent_token=self.quote_asset),
            fill_timestamp=1,
        )

        self.assertTrue(order.update_with_trade_update(trade_update))
        self.assertEqual(order.executed_amount_base, trade_update.fill_base_amount)
        self.assertEqual(order.executed_amount_quote, trade_update.fill_quote_amount)
        self.assertEqual(order.last_update_timestamp, trade_update.fill_timestamp)
        self.assertEqual(1, len(order.order_fills))
        self.assertIn(trade_update.trade_id, order.order_fills)

    def test_update_with_trade_update_duplicate_trade_update(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        trade_update: TradeUpdate = TradeUpdate(
            trade_id="someTradeId",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            fill_price=Decimal("1.0"),
            fill_base_amount=Decimal("500.0"),
            fill_quote_amount=Decimal("500.0"),
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(token=self.quote_asset, amount=self.trade_fee_percent * Decimal("500.0"))]),
            fill_timestamp=1,
        )

        self.assertTrue(order.update_with_trade_update(trade_update))
        self.assertEqual(order.executed_amount_base, trade_update.fill_base_amount)
        self.assertEqual(order.executed_amount_quote, trade_update.fill_quote_amount)
        self.assertEqual(order.last_update_timestamp, trade_update.fill_timestamp)
        self.assertEqual(1, len(order.order_fills))
        self.assertIn(trade_update.trade_id, order.order_fills)

        # Ignores duplicate trade update
        self.assertFalse(order.update_with_trade_update(trade_update))

    def test_update_with_trade_update_multiple_trade_updates(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        initial_fill_price: Decimal = Decimal("0.5")
        initial_fill_amount: Decimal = Decimal("500.0")
        trade_update_1: TradeUpdate = TradeUpdate(
            trade_id="someTradeId_1",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            fill_price=initial_fill_price,
            fill_base_amount=initial_fill_amount,
            fill_quote_amount=initial_fill_price * initial_fill_amount,
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(token=self.quote_asset, amount=self.trade_fee_percent * initial_fill_amount)]),
            fill_timestamp=1,
        )

        subsequent_fill_price: Decimal = Decimal("1.0")
        subsequent_fill_amount: Decimal = Decimal("500.0")
        trade_update_2: TradeUpdate = TradeUpdate(
            trade_id="someTradeId_2",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            fill_price=subsequent_fill_price,
            fill_base_amount=subsequent_fill_amount,
            fill_quote_amount=subsequent_fill_price * subsequent_fill_amount,
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(token=self.quote_asset, amount=self.trade_fee_percent * subsequent_fill_amount)]),
            fill_timestamp=2,
        )

        self.assertTrue(order.update_with_trade_update(trade_update_1))
        self.assertIn(trade_update_1.trade_id, order.order_fills)
        self.assertEqual(order.executed_amount_base, trade_update_1.fill_base_amount)
        self.assertEqual(order.executed_amount_quote, trade_update_1.fill_quote_amount)
        self.assertEqual(order.last_update_timestamp, trade_update_1.fill_timestamp)
        self.assertEqual(1, len(order.order_fills))

        self.assertTrue(order.is_open)

        self.assertTrue(order.update_with_trade_update(trade_update_2))
        self.assertIn(trade_update_2.trade_id, order.order_fills)
        self.assertEqual(order.executed_amount_base, order.amount)
        self.assertEqual(
            order.executed_amount_quote, trade_update_1.fill_quote_amount + trade_update_2.fill_quote_amount
        )
        self.assertEqual(order.last_update_timestamp, trade_update_2.fill_timestamp)
        self.assertEqual(2, len(order.order_fills))
        self.assertEqual(
            order.average_executed_price,
            (trade_update_1.fill_quote_amount + trade_update_2.fill_quote_amount) / order.amount,
        )

        self.assertTrue(order.is_filled)
        self.assertEqual(order.current_state, OrderState.PENDING_CREATE)

    def test_trade_update_does_not_change_exchange_order_id(self):
        order: InFlightOrder = InFlightOrder(
            client_order_id=self.client_order_id,
            trading_pair=self.trading_pair,
            order_type=OrderType.LIMIT,
            trade_type=TradeType.BUY,
            amount=Decimal("1000.0"),
            creation_timestamp=1640001112.0,
            price=Decimal("1.0"),
        )

        trade_update: TradeUpdate = TradeUpdate(
            trade_id="someTradeId",
            client_order_id=self.client_order_id,
            exchange_order_id=self.exchange_order_id,
            trading_pair=self.trading_pair,
            fill_price=Decimal("1.0"),
            fill_base_amount=Decimal("500.0"),
            fill_quote_amount=Decimal("500.0"),
            fee=AddedToCostTradeFee(
                flat_fees=[TokenAmount(token=self.quote_asset, amount=self.trade_fee_percent * Decimal("500.0"))]),
            fill_timestamp=1,
        )

        self.assertTrue(order.update_with_trade_update(trade_update))
        self.assertIsNone(order.exchange_order_id)
        self.assertFalse(order.exchange_order_id_update_event.is_set())
