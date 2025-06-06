import unittest
from decimal import Decimal
from pathlib import Path
from typing import Dict
from unittest.mock import patch

import yaml

from hummingbot.client.config.config_helpers import ClientConfigAdapter, ConfigValidationError
from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.settings import AllConnectorSettings, ConnectorSetting, ConnectorType
from hummingbot.core.data_type.trade_fee import TradeFeeSchema
from hummingbot.strategy.cross_exchange_market_making.cross_exchange_market_making_config_map_pydantic import (
    ActiveOrderRefreshMode,
    CrossExchangeMarketMakingConfigMap,
    OracleConversionRateMode,
    PassiveOrderRefreshMode,
    TakerToMakerConversionRateMode,
)


class CrossExchangeMarketMakingConfigMapPydanticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.base_asset = "COINALPHA"
        cls.quote_asset = "HBOT"
        cls.trading_pair = f"{cls.base_asset}-{cls.quote_asset}"

        cls.maker_exchange = "mock_paper_exchange"
        cls.taker_exchange = "mock_paper_exchange"

        # Reset the list of connectors (there could be changes introduced by other tests when running the suite
        AllConnectorSettings.create_connector_settings()

    def setUp(self) -> None:
        super().setUp()

        self._get_exchange_names_patcher = patch("hummingbot.client.settings.AllConnectorSettings.get_exchange_names")
        self._get_connector_settings_patcher = patch(
            "hummingbot.client.settings.AllConnectorSettings.get_connector_settings")

        get_exchange_names_mock = self._get_exchange_names_patcher.start()
        get_exchange_names_mock.return_value = set(self.get_mock_connector_settings().keys())

        get_connector_settings_mock = self._get_connector_settings_patcher.start()
        get_connector_settings_mock.return_value = self.get_mock_connector_settings()

        self._original_paper_trade_exchanges = AllConnectorSettings.paper_trade_connectors_names
        AllConnectorSettings.paper_trade_connectors_names.append("mock_paper_exchange")

        config_settings = self.get_default_map()

        self.config_map = ClientConfigAdapter(CrossExchangeMarketMakingConfigMap(**config_settings))

    def tearDown(self) -> None:
        self._get_connector_settings_patcher.stop()
        self._get_exchange_names_patcher.stop()
        if self._original_paper_trade_exchanges is not None:
            AllConnectorSettings.paper_trade_connectors_names = self._original_paper_trade_exchanges
        super().tearDown()

    def get_default_map(self) -> Dict[str, str]:
        config_settings = {
            "maker_market": self.maker_exchange,
            "taker_market": self.taker_exchange,
            "maker_market_trading_pair": self.trading_pair,
            "taker_market_trading_pair": self.trading_pair,
            "order_amount": "10",
            "min_profitability": "0",
        }
        return config_settings

    def get_mock_connector_settings(self):

        conf_var_connector_maker = ConfigVar(key='mock_paper_exchange', prompt="")
        conf_var_connector_maker.value = 'mock_paper_exchange'

        conf_var_connector_taker = ConfigVar(key='mock_paper_exchange', prompt="")
        conf_var_connector_taker.value = 'mock_paper_exchange'

        settings = {
            "mock_paper_exchange": ConnectorSetting(
                name='mock_paper_exchange',
                type=ConnectorType.Exchange,
                example_pair='ZRX-ETH',
                centralised=True,
                use_ethereum_wallet=False,
                trade_fee_schema=TradeFeeSchema(
                    percent_fee_token=None,
                    maker_percent_fee_decimal=Decimal('0.001'),
                    taker_percent_fee_decimal=Decimal('0.001'),
                    buy_percent_fee_deducted_from_returns=False,
                    maker_fixed_fees=[],
                    taker_fixed_fees=[]),
                config_keys={
                    'connector': conf_var_connector_maker
                },
                is_sub_domain=False,
                parent_name=None,
                domain_parameter=None,
                use_eth_gas_lookup=False)
        }

        return settings

    def test_top_depth_tolerance_prompt(self):
        self.config_map.maker_market_trading_pair = self.trading_pair
        prompt = self.config_map.top_depth_tolerance_prompt(self.config_map)
        expected = f"What is your top depth tolerance? (in {self.base_asset})"

        self.assertEqual(expected, prompt)

    def test_order_amount_prompt(self):
        self.config_map.maker_market_trading_pair = self.trading_pair
        prompt = self.config_map.order_amount_prompt(self.config_map)
        expected = f"What is the amount of {self.base_asset} per order?"

        self.assertEqual(expected, prompt)

    @patch("hummingbot.client.config.strategy_config_data_types.validate_market_trading_pair")
    def test_validators(self, _):
        self.config_map.order_refresh_mode = "active_order_refresh"
        self.assertIsInstance(self.config_map.order_refresh_mode.hb_config, ActiveOrderRefreshMode)

        self.config_map.order_refresh_mode = "passive_order_refresh"
        self.config_map.order_refresh_mode.cancel_order_threshold = Decimal("1.0")
        self.config_map.order_refresh_mode.cancel_order_threshold = Decimal("2.0")
        self.assertIsInstance(self.config_map.order_refresh_mode.hb_config, PassiveOrderRefreshMode)

        with self.assertRaises(ConfigValidationError) as e:
            self.config_map.order_refresh_mode = "XXX"

        error_msg = (
            "Value error, Invalid order refresh mode, please choose value from ['passive_order_refresh', 'active_order_refresh']."
        )
        self.assertEqual(error_msg, str(e.exception))

        self.config_map.conversion_rate_mode = "rate_oracle_conversion_rate"
        self.assertIsInstance(self.config_map.conversion_rate_mode.hb_config, OracleConversionRateMode)

        self.config_map.conversion_rate_mode = "fixed_conversion_rate"
        self.config_map.conversion_rate_mode.taker_to_maker_base_conversion_rate = Decimal("1.0")
        self.config_map.conversion_rate_mode.taker_to_maker_quote_conversion_rate = Decimal("2.0")
        self.assertIsInstance(self.config_map.conversion_rate_mode.hb_config, TakerToMakerConversionRateMode)

        with self.assertRaises(ConfigValidationError) as e:
            self.config_map.conversion_rate_mode = "XXX"

        error_msg = (
            "Value error, Invalid conversion rate mode, please choose value from ['rate_oracle_conversion_rate', 'fixed_conversion_rate']."
        )
        self.assertEqual(error_msg, str(e.exception))

    @patch("hummingbot.client.settings.AllConnectorSettings.get_exchange_names")
    @patch("hummingbot.client.settings.AllConnectorSettings.get_connector_settings")
    def test_load_configs_from_yaml(self, get_connector_settings_mock, get_exchange_names_mock):

        get_exchange_names_mock.return_value = set(self.get_mock_connector_settings().keys())
        get_connector_settings_mock.return_value = self.get_mock_connector_settings()

        cur_dir = Path(__file__).parent
        f_path = cur_dir / "test_config.yml"

        with open(f_path, "r") as file:
            data = yaml.safe_load(file)

        loaded_config_map = ClientConfigAdapter(CrossExchangeMarketMakingConfigMap(**data))

        self.assertEqual(self.config_map, loaded_config_map)
