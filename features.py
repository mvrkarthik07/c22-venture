from __future__ import annotations

import math
from bisect import insort
from collections import deque
from typing import Any, Mapping

import numpy as np
import pandas as pd


class TraderState:
    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})
        self.start_balance = float(self.config.get("start_balance", 10000.0))
        self.trader_key = self._config_value("trader_key", "traderKey")
        self._prior_campaigns_value = self._config_value("prior_campaigns")
        self._prior_campaign_ids = set(
            self._config_value("prior_campaign_ids", "campaign_history", default=[]) or []
        )
        self.shared_ip = self._bool_config("shared_ip", "sharedIpFlag")
        self.ip_cluster_size = self._numeric_or_nan(
            self._config_value("ip_cluster_size", "ipClusterSize")
        )
        challenge_type = self._config_value("challenge_type", "challenge_type_id")
        self.challenge_type = "unknown" if self._is_missing(challenge_type) else challenge_type
        self.gold_vol_prev_day = self._resolve_gold_vol_prev_day()

        self.trade_count = 0
        self.cum_net_profit = 0.0
        self.peak_equity = self.start_balance
        self.loss_streak = 0
        self.win_streak = 0
        self.pnl_ewm = 0.0
        self.first_open_time: pd.Timestamp | None = None
        self.last_close_time: pd.Timestamp | None = None
        self.current_loss_streak_start_open: pd.Timestamp | None = None
        self.pre_loss_streak_amount_mean = np.nan

        self.amount_count = 0
        self.amount_mean = 0.0
        self.amount_m2 = 0.0
        self.sorted_amounts: list[float] = []
        self.prior_gap_seconds: list[float] = []
        self.last5_has_sl: deque[bool] = deque(maxlen=5)
        self.last5_manual_exit: deque[bool] = deque(maxlen=5)

    def compute_features(self, position) -> dict:
        open_time = self._timestamp(self._value(position, "openDateTime"))
        amount = float(self._value(position, "amount"))
        open_price = self._numeric_or_nan(self._value(position, "openPrice"))
        sl_price = self._value(position, "slPrice")
        tp_price = self._value(position, "tpPrice")

        lot_zscore = np.nan
        if self.amount_count >= 3:
            variance = self.amount_m2 / self.amount_count
            std = math.sqrt(variance) if variance > 0 else np.nan
            if not np.isnan(std):
                lot_zscore = (amount - self.amount_mean) / std

        size_after_loss_delta = np.nan
        if self.loss_streak > 0 and not np.isnan(self.pre_loss_streak_amount_mean):
            size_after_loss_delta = amount - self.pre_loss_streak_amount_mean

        has_sl = not self._is_missing(sl_price)
        has_tp = not self._is_missing(tp_price)

        sl_distance_pct = np.nan
        if has_sl and not np.isnan(open_price) and open_price != 0:
            sl_distance_pct = abs(open_price - float(sl_price)) / open_price

        sl_usage_rate_5 = np.nan
        if len(self.last5_has_sl) >= 3:
            sl_usage_rate_5 = float(np.mean(self.last5_has_sl))

        manual_exit_rate_5 = np.nan
        if len(self.last5_manual_exit) >= 3:
            manual_exit_rate_5 = float(np.mean(self.last5_manual_exit))

        equity = self.start_balance + self.cum_net_profit
        pnl_pct = self.cum_net_profit / self.start_balance
        dd_from_peak_pct = (self.peak_equity - equity) / self.start_balance
        trade_index = self.trade_count + 1

        log_dt_close = np.nan
        dt_since_last_close = np.nan
        if self.last_close_time is not None:
            dt_since_last_close = max(
                (open_time - self.last_close_time).total_seconds(),
                0.0,
            )
            log_dt_close = math.log1p(dt_since_last_close)

        first_open = self.first_open_time or open_time
        hours_since_first_open = max(
            (open_time - first_open).total_seconds() / 3600.0,
            1.0 / 60.0,
        )

        prior_campaigns = self._resolve_prior_campaigns(position)

        return {
            "loss_streak": self.loss_streak,
            "win_streak": self.win_streak,
            "pnl_ewm": self.pnl_ewm,
            "lot_zscore": lot_zscore,
            "amount": amount,
            "size_after_loss_delta": size_after_loss_delta,
            "has_sl": has_sl,
            "has_tp": has_tp,
            "sl_distance_pct": sl_distance_pct,
            "sl_usage_rate_5": sl_usage_rate_5,
            "manual_exit_rate_5": manual_exit_rate_5,
            "pnl_pct": pnl_pct,
            "dd_from_peak_pct": dd_from_peak_pct,
            "trade_index": trade_index,
            "log_dt_close": log_dt_close,
            "trades_per_hour": trade_index / hours_since_first_open,
            "prior_campaigns": prior_campaigns,
            "shared_ip": self.shared_ip,
            "ip_cluster_size": self.ip_cluster_size,
            "challenge_type": self.challenge_type,
            "gold_vol_prev_day": self.gold_vol_prev_day,
        }

    def update(self, position) -> None:
        open_time = self._timestamp(self._value(position, "openDateTime"))
        close_time = self._timestamp(self._value(position, "closeDateTime"))
        amount = float(self._value(position, "amount"))
        net_profit = float(self._value(position, "netProfit"))
        exit_type = self._value(position, "exit_type", default=None)

        if self.first_open_time is None:
            self.first_open_time = open_time

        if self.last_close_time is not None:
            gap_seconds = max((open_time - self.last_close_time).total_seconds(), 0.0)
            self.prior_gap_seconds.append(gap_seconds)

        if net_profit < 0:
            if self.loss_streak == 0:
                self.current_loss_streak_start_open = open_time
                self.pre_loss_streak_amount_mean = (
                    self.amount_mean if self.amount_count else np.nan
                )
            self.loss_streak += 1
            self.win_streak = 0
        elif net_profit > 0:
            self.loss_streak = 0
            self.win_streak += 1
            self.current_loss_streak_start_open = None
            self.pre_loss_streak_amount_mean = np.nan
        else:
            self.loss_streak = 0
            self.win_streak = 0
            self.current_loss_streak_start_open = None
            self.pre_loss_streak_amount_mean = np.nan

        self.pnl_ewm = 0.3 * net_profit + 0.7 * self.pnl_ewm
        self.cum_net_profit += net_profit
        self.peak_equity = max(self.peak_equity, self.start_balance + self.cum_net_profit)
        self.trade_count += 1

        self._update_amount_stats(amount)
        self.last5_has_sl.append(not self._is_missing(self._value(position, "slPrice")))
        self.last5_manual_exit.append(exit_type == "manual")
        self.last_close_time = close_time

    def _update_amount_stats(self, amount: float) -> None:
        self.amount_count += 1
        delta = amount - self.amount_mean
        self.amount_mean += delta / self.amount_count
        delta2 = amount - self.amount_mean
        self.amount_m2 += delta * delta2
        insort(self.sorted_amounts, amount)

    def _resolve_prior_campaigns(self, position) -> int:
        if self._prior_campaigns_value is not None and not self._is_missing(self._prior_campaigns_value):
            return int(self._prior_campaigns_value)
        if self._is_missing(self.trader_key):
            return 0
        current_campaign = self._config_value("campaign_id", "campaignId")
        if current_campaign is None:
            current_campaign = self._value(position, "campaignId", default=None)
        if current_campaign is None:
            return 0
        return sum(1 for campaign_id in self._prior_campaign_ids if campaign_id < current_campaign)

    def _resolve_gold_vol_prev_day(self):
        direct = self._config_value("gold_vol_prev_day")
        if not self._is_missing(direct):
            return float(direct)

        lookup = self._config_value("gold_vol_prev_day_lookup", default=None)
        campaign_date = self._config_value("campaign_date", "campaignDate", default=None)
        if lookup is None or self._is_missing(campaign_date):
            return np.nan

        prev_day = (pd.Timestamp(campaign_date).normalize() - pd.Timedelta(days=1)).date()
        for key in (prev_day, pd.Timestamp(prev_day), str(prev_day)):
            if key in lookup and not self._is_missing(lookup[key]):
                return float(lookup[key])
        return np.nan

    def _config_value(self, *keys, default=None):
        for key in keys:
            if key in self.config:
                return self.config[key]
        return default

    @staticmethod
    def _value(position, key: str, default=...):
        if isinstance(position, Mapping):
            if key in position:
                return position[key]
        elif hasattr(position, key):
            return getattr(position, key)
        else:
            try:
                return position[key]
            except Exception:
                pass
        if default is ...:
            raise KeyError(key)
        return default

    @staticmethod
    def _timestamp(value) -> pd.Timestamp:
        return pd.Timestamp(value)

    @staticmethod
    def _is_missing(value) -> bool:
        return bool(pd.isna(value))

    @staticmethod
    def _numeric_or_nan(value) -> float:
        if pd.isna(value):
            return np.nan
        return float(value)

    def _bool_config(self, *keys) -> bool:
        value = self._config_value(*keys, default=False)
        return False if self._is_missing(value) else bool(value)
