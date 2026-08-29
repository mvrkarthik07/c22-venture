from __future__ import annotations

import math
from bisect import insort
from collections import deque
from typing import Any, Mapping

import numpy as np
import pandas as pd


def fit_entry_gap_sec_clip(values, quantile: float = 0.99) -> float:
    clean = pd.Series(values, dtype="float64").dropna()
    if clean.empty:
        return np.nan
    return float(clean.quantile(quantile))


class TraderHistory:
    TILT_HALFLIFE_CAMPAIGNS = 2.0
    SURVIVAL_SPAN_MEDIAN_HOURS = 1.99

    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})
        self.shrinkage_k = float(self.config.get("shrinkage_k", 5.0))
        self.population_trader_prior_tilt = self._numeric_or_nan(
            self.config.get("population_trader_prior_tilt", np.nan)
        )
        self.population_trader_prior_sl_discipline = self._numeric_or_nan(
            self.config.get("population_trader_prior_sl_discipline", np.nan)
        )
        self.population_trader_prior_survival = self._numeric_or_nan(
            self.config.get("population_trader_prior_survival", np.nan)
        )

        self.completed_campaign_ids: list[int] = []
        self.prior_tilt_campaign_means: list[float] = []
        self.prior_tilt_position_count = 0
        self.prior_sl_distance_sum = 0.0
        self.prior_sl_position_count = 0
        self.prior_survival_span_hours_sum = 0.0
        self.prior_survival_campaign_count = 0
        self.prior_survival_position_count = 0

    def compute_features(self, current_campaign_id: int) -> dict[str, Any]:
        self._assert_prior_only(current_campaign_id)

        prior_campaigns = len(self.completed_campaign_ids)
        trader_prior_tilt_raw = self._ewma(
            self.prior_tilt_campaign_means,
            halflife=self.TILT_HALFLIFE_CAMPAIGNS,
        )
        trader_prior_sl_discipline_raw = np.nan
        if self.prior_sl_position_count > 0:
            trader_prior_sl_discipline_raw = (
                self.prior_sl_distance_sum / self.prior_sl_position_count
            )

        trader_prior_survival_raw = np.nan
        if self.prior_survival_campaign_count > 0:
            trader_prior_survival_raw = (
                self.prior_survival_span_hours_sum / self.prior_survival_campaign_count
            ) / self.SURVIVAL_SPAN_MEDIAN_HOURS

        return {
            "prior_campaigns": prior_campaigns,
            "trader_prior_tilt": self._shrink(
                trader_prior_tilt_raw,
                self.population_trader_prior_tilt,
                self.prior_tilt_position_count,
            ),
            "trader_prior_sl_discipline": self._shrink(
                trader_prior_sl_discipline_raw,
                self.population_trader_prior_sl_discipline,
                self.prior_sl_position_count,
            ),
            "trader_prior_survival": self._shrink(
                trader_prior_survival_raw,
                self.population_trader_prior_survival,
                self.prior_survival_position_count,
            ),
            "is_cold_start": prior_campaigns == 0,
        }

    def update_campaign(self, campaign_id: int, summary: Mapping[str, Any]) -> None:
        if self.completed_campaign_ids and campaign_id <= self.completed_campaign_ids[-1]:
            raise AssertionError(
                f"TraderHistory campaign order violation: got {campaign_id} after "
                f"{self.completed_campaign_ids[-1]}"
            )

        tilt_mean = self._numeric_or_nan(summary.get("tilt_mean"))
        tilt_n = int(summary.get("tilt_n", 0))
        if tilt_n > 0 and not np.isnan(tilt_mean):
            self.prior_tilt_campaign_means.append(tilt_mean)
            self.prior_tilt_position_count += tilt_n

        sl_sum = self._numeric_or_nan(summary.get("sl_sum"))
        sl_n = int(summary.get("sl_n", 0))
        if sl_n > 0 and not np.isnan(sl_sum):
            self.prior_sl_distance_sum += sl_sum
            self.prior_sl_position_count += sl_n

        survival_span_hours = self._numeric_or_nan(summary.get("survival_span_hours"))
        survival_n = int(summary.get("survival_n", 0))
        if survival_n > 0 and not np.isnan(survival_span_hours):
            self.prior_survival_span_hours_sum += survival_span_hours
            self.prior_survival_campaign_count += 1
            self.prior_survival_position_count += survival_n

        self.completed_campaign_ids.append(int(campaign_id))

    def _assert_prior_only(self, current_campaign_id: int) -> None:
        if any(campaign_id >= current_campaign_id for campaign_id in self.completed_campaign_ids):
            raise AssertionError(
                "TraderHistory contains same-campaign or future-campaign state for "
                f"current campaign {current_campaign_id}"
            )

    def _shrink(self, trader_estimate: float, population_mean: float, n: int) -> float:
        if np.isnan(population_mean):
            return trader_estimate
        if n <= 0 or np.isnan(trader_estimate):
            return population_mean
        weight = n / (n + self.shrinkage_k)
        return weight * trader_estimate + (1.0 - weight) * population_mean

    @staticmethod
    def _ewma(values: list[float], halflife: float) -> float:
        if not values:
            return np.nan
        alpha = 1.0 - math.exp(math.log(0.5) / halflife)
        ewma = values[0]
        for value in values[1:]:
            ewma = alpha * value + (1.0 - alpha) * ewma
        return ewma

    @staticmethod
    def _numeric_or_nan(value) -> float:
        if pd.isna(value):
            return np.nan
        return float(value)


class TraderState:
    def __init__(self, config: Mapping[str, Any] | None = None):
        self.config = dict(config or {})
        self.start_balance = self._numeric_or_nan(self._config_value("start_balance", default=np.nan))
        self.has_start_balance = not np.isnan(self.start_balance) and self.start_balance != 0.0
        self.breach_threshold_usd = self._numeric_or_nan(
            self._config_value("breach_threshold_usd", default=np.nan)
        )
        self.target_threshold_usd = self._numeric_or_nan(
            self._config_value("target_threshold_usd", default=np.nan)
        )
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
        self.entry_gap_sec_clip = self._numeric_or_nan(
            self._config_value("entry_gap_sec_clip", default=np.nan)
        )
        self.trader_prior_tilt = self._numeric_or_nan(
            self._config_value("trader_prior_tilt", default=np.nan)
        )
        self.trader_prior_sl_discipline = self._numeric_or_nan(
            self._config_value("trader_prior_sl_discipline", default=np.nan)
        )
        self.trader_prior_survival = self._numeric_or_nan(
            self._config_value("trader_prior_survival", default=np.nan)
        )
        self.is_cold_start = self._bool_config("is_cold_start")

        self.trade_count = 0
        self.cum_net_profit = 0.0
        self.peak_cum_net_profit = 0.0
        self.loss_streak = 0
        self.win_streak = 0
        self.pnl_ewm = 0.0
        self.first_open_time: pd.Timestamp | None = None
        self.last_close_time: pd.Timestamp | None = None
        self.current_loss_streak_start_open: pd.Timestamp | None = None
        self.pre_loss_streak_amount_mean = np.nan
        self.last_side = None
        self.last_net_profit = np.nan
        self.last_amount = np.nan

        self.amount_count = 0
        self.amount_mean = 0.0
        self.amount_m2 = 0.0
        self.sorted_amounts: list[float] = []
        self.prior_gap_seconds: list[float] = []
        self.prior_sl_distance_pcts: list[float] = []
        self.last5_has_sl: deque[bool] = deque(maxlen=5)
        self.last5_manual_exit: deque[bool] = deque(maxlen=5)

    def compute_features(self, position) -> dict:
        open_time = self._timestamp(self._value(position, "openDateTime"))
        amount = float(self._value(position, "amount"))
        sl_price = self._value(position, "slPrice")
        tp_price = self._value(position, "tpPrice")
        side = self._value(position, "side", default=None)

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

        sl_distance_pct = self._sl_distance_pct(position)

        sl_widening_delta = np.nan
        if has_sl and len(self.prior_sl_distance_pcts) >= 3 and not np.isnan(sl_distance_pct):
            sl_widening_delta = sl_distance_pct - self._median_from_sorted(
                self.prior_sl_distance_pcts
            )

        sl_usage_rate_5 = np.nan
        if len(self.last5_has_sl) >= 3:
            sl_usage_rate_5 = float(np.mean(self.last5_has_sl))

        manual_exit_rate_5 = np.nan
        if len(self.last5_manual_exit) >= 3:
            manual_exit_rate_5 = float(np.mean(self.last5_manual_exit))

        cum_pnl_usd = self.cum_net_profit
        dd_from_peak_usd = self.peak_cum_net_profit - self.cum_net_profit
        pnl_pct = np.nan
        dd_from_peak_pct = np.nan
        if self.has_start_balance:
            pnl_pct = cum_pnl_usd / self.start_balance
            dd_from_peak_pct = dd_from_peak_usd / self.start_balance

        breach_proximity_usd = np.nan
        if not np.isnan(self.breach_threshold_usd):
            breach_proximity_usd = self.breach_threshold_usd - dd_from_peak_usd

        target_proximity_usd = np.nan
        if not np.isnan(self.target_threshold_usd):
            target_proximity_usd = self.target_threshold_usd - cum_pnl_usd

        trade_index = self.trade_count + 1

        log_dt_close = np.nan
        dt_since_last_close = np.nan
        if self.last_close_time is not None:
            dt_since_last_close = max(
                (open_time - self.last_close_time).total_seconds(),
                0.0,
            )
            log_dt_close = math.log1p(dt_since_last_close)

        entry_gap_sec = dt_since_last_close
        if not np.isnan(entry_gap_sec) and not np.isnan(self.entry_gap_sec_clip):
            entry_gap_sec = min(entry_gap_sec, self.entry_gap_sec_clip)

        same_direction_reentry = int(
            self.trade_count > 0
            and self.last_net_profit < 0
            and side == self.last_side
        )

        size_delta_ratio = np.nan
        if self.trade_count > 0 and not np.isnan(self.last_amount) and self.last_amount != 0.0:
            size_delta_ratio = amount / self.last_amount

        first_open = self.first_open_time or open_time
        hours_since_first_open = max(
            (open_time - first_open).total_seconds() / 3600.0,
            1.0 / 60.0,
        )

        prior_campaigns = self._resolve_prior_campaigns(position)
        loss_streak_ge_2 = int(self.loss_streak >= 2)

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
            "cum_pnl_usd": cum_pnl_usd,
            "dd_from_peak_usd": dd_from_peak_usd,
            "breach_proximity_usd": breach_proximity_usd,
            "target_proximity_usd": target_proximity_usd,
            "trade_index": trade_index,
            "log_dt_close": log_dt_close,
            "trades_per_hour": trade_index / hours_since_first_open,
            "prior_campaigns": prior_campaigns,
            "prior_campaigns_x_loss_streak_ge_2": prior_campaigns * loss_streak_ge_2,
            "shared_ip": self.shared_ip,
            "ip_cluster_size": self.ip_cluster_size,
            "challenge_type": self.challenge_type,
            "gold_vol_prev_day": self.gold_vol_prev_day,
            "sl_widening_delta": sl_widening_delta,
            "entry_gap_sec": entry_gap_sec,
            "same_direction_reentry": same_direction_reentry,
            "size_delta_ratio": size_delta_ratio,
            "trader_prior_tilt": self.trader_prior_tilt,
            "trader_prior_sl_discipline": self.trader_prior_sl_discipline,
            "trader_prior_survival": self.trader_prior_survival,
            "is_cold_start": self.is_cold_start,
        }

    def compute_v2_features(self, position) -> dict:
        """Compute only the frozen Stage 3 V2 fields at entry time.

        This deliberately does not read current-trade SL/TP or any close-time
        field.  Those values are consumed only by ``update`` after the decision
        has been made, so prior closed-position rates remain causal while the
        current trade cannot leak its outcome into the prediction.
        """
        open_time = self._timestamp(self._value(position, "openDateTime"))
        amount = float(self._value(position, "amount"))
        side = self._value(position, "side", default=None)

        lot_zscore = np.nan
        if self.amount_count >= 3:
            variance = self.amount_m2 / self.amount_count
            std = math.sqrt(variance) if variance > 0 else np.nan
            if not np.isnan(std):
                lot_zscore = (amount - self.amount_mean) / std

        size_after_loss_delta = np.nan
        if self.loss_streak > 0 and not np.isnan(self.pre_loss_streak_amount_mean):
            size_after_loss_delta = amount - self.pre_loss_streak_amount_mean

        sl_usage_rate_5 = np.nan
        if len(self.last5_has_sl) >= 3:
            sl_usage_rate_5 = float(np.mean(self.last5_has_sl))

        manual_exit_rate_5 = np.nan
        if len(self.last5_manual_exit) >= 3:
            manual_exit_rate_5 = float(np.mean(self.last5_manual_exit))

        cum_pnl_usd = self.cum_net_profit
        dd_from_peak_usd = self.peak_cum_net_profit - self.cum_net_profit
        pnl_pct = np.nan
        dd_from_peak_pct = np.nan
        if self.has_start_balance:
            pnl_pct = cum_pnl_usd / self.start_balance
            dd_from_peak_pct = dd_from_peak_usd / self.start_balance

        trade_index = self.trade_count + 1
        log_dt_close = np.nan
        if self.last_close_time is not None:
            log_dt_close = math.log1p(
                max((open_time - self.last_close_time).total_seconds(), 0.0)
            )

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
            "sl_usage_rate_5": sl_usage_rate_5,
            "manual_exit_rate_5": manual_exit_rate_5,
            "pnl_pct": pnl_pct,
            "dd_from_peak_pct": dd_from_peak_pct,
            "trade_index": trade_index,
            "log_dt_close": log_dt_close,
            "trades_per_hour": trade_index / hours_since_first_open,
            "prior_campaigns_x_loss_streak_ge_2": prior_campaigns * int(self.loss_streak >= 2),
            "shared_ip": self.shared_ip,
            "ip_cluster_size": self.ip_cluster_size,
            "challenge_type": self.challenge_type,
            "gold_vol_prev_day": self.gold_vol_prev_day,
            "same_direction_reentry": int(
                self.trade_count > 0
                and self.last_net_profit < 0
                and side == self.last_side
            ),
            "size_delta_ratio": (
                amount / self.last_amount
                if self.trade_count > 0
                and not np.isnan(self.last_amount)
                and self.last_amount != 0.0
                else np.nan
            ),
        }

    def update(self, position) -> None:
        open_time = self._timestamp(self._value(position, "openDateTime"))
        close_time = self._timestamp(self._value(position, "closeDateTime"))
        amount = float(self._value(position, "amount"))
        net_profit = float(self._value(position, "netProfit"))
        exit_type = self._value(position, "exit_type", default=None)
        side = self._value(position, "side", default=None)

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
        self.peak_cum_net_profit = max(self.peak_cum_net_profit, self.cum_net_profit)
        self.trade_count += 1

        self._update_amount_stats(amount)
        sl_distance_pct = self._sl_distance_pct(position)
        if not np.isnan(sl_distance_pct):
            insort(self.prior_sl_distance_pcts, sl_distance_pct)
        self.last5_has_sl.append(not self._is_missing(self._value(position, "slPrice")))
        self.last5_manual_exit.append(exit_type == "manual")
        self.last_close_time = close_time
        self.last_side = side
        self.last_net_profit = net_profit
        self.last_amount = amount

    def _update_amount_stats(self, amount: float) -> None:
        self.amount_count += 1
        delta = amount - self.amount_mean
        self.amount_mean += delta / self.amount_count
        delta2 = amount - self.amount_mean
        self.amount_m2 += delta * delta2
        insort(self.sorted_amounts, amount)

    def _sl_distance_pct(self, position) -> float:
        open_price = self._numeric_or_nan(self._value(position, "openPrice"))
        sl_price = self._value(position, "slPrice")
        if self._is_missing(sl_price) or np.isnan(open_price) or open_price == 0:
            return np.nan
        return abs(open_price - float(sl_price)) / open_price

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

    @staticmethod
    def _median_from_sorted(values: list[float]) -> float:
        count = len(values)
        if count == 0:
            return np.nan
        mid = count // 2
        if count % 2 == 1:
            return values[mid]
        return 0.5 * (values[mid - 1] + values[mid])

    def _bool_config(self, *keys) -> bool:
        value = self._config_value(*keys, default=False)
        return False if self._is_missing(value) else bool(value)
