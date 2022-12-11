from datetime import timedelta, datetime, date, time
from zoneinfo import ZoneInfo

from pandas import Timestamp
from pytz import timezone
from typing import Dict, List, Optional
from copy import deepcopy

import pandas as pd
from pandas.tseries.frequencies import to_offset
import akshare as ak

from vnpy.trader.setting import SETTINGS
from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.utility import round_to

# 数据频率映射
INTERVAL_VT2TS = {
    Interval.MINUTE: "1min",
    Interval.HOUR: "60min",
    Interval.DAILY: "D",
    Interval.WEEKLY: "W"
}

# 股票支持列表
STOCK_LIST = [
    Exchange.SEHK
]

# 期货支持列表
FUTURE_LIST = [
]

# 交易所映射
EXCHANGE_VT2TS = {
    Exchange.SEHK: "HK",
    Exchange.SSE: "SH",
    Exchange.SZSE: "SZ",
}

# 时间调整映射
INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta(),
    Interval.WEEKLY: timedelta()
}

# 中国上海时区
CHINA_TZ = ZoneInfo("Asia/Shanghai")


func_price_map = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': lambda x: x.sum(min_count=1)}


def to_ts_symbol(symbol, exchange) -> Optional[str]:
    """将交易所代码转换为akshare代码"""
    # 股票
    if exchange in STOCK_LIST:
        # ts_symbol = f"{symbol}.{EXCHANGE_VT2TS[exchange]}"
        ts_symbol = f"0{symbol}"
    # 期货
    elif exchange in FUTURE_LIST:
        ts_symbol = f"{symbol}.{EXCHANGE_VT2TS[exchange]}".upper()
    else:
        return None

    return ts_symbol


def to_ts_asset(symbol, exchange) -> Optional[str]:
    """生成akshare资产类别"""
    # 股票
    if exchange in STOCK_LIST:
        asset = "E"
    # 期货
    elif exchange in FUTURE_LIST:
        asset = "FT"
    else:
        return None

    return asset


class AkshareDatafeed(BaseDatafeed):
    """akshare数据服务接口"""

    def __init__(self, username=None, password=None):
        """"""
        self.username: str = SETTINGS["datafeed.username"] if username is None else username
        self.password: str = SETTINGS["datafeed.password"] if password is None else password

        self.inited: bool = False

    def init(self) -> bool:
        """初始化"""
        if self.inited:
            return True

        # ak.set_token(self.password)
        # self.pro = ak.pro_api()
        self.inited = True

        return True

    def query_bar_history(self, req: HistoryRequest) -> Optional[List[BarData]]:
        """查询k线数据"""
        if not self.inited:
            self.init()

        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        ak_symbol = to_ts_symbol(symbol, exchange)
        if not ak_symbol:
            return None

        ts_interval = INTERVAL_VT2TS.get(interval)
        if not ts_interval:
            return None

        try:
            d1 = ak.stock_hk_daily(
                symbol=ak_symbol,
                adjust='qfq'
            )
        except IOError:
            return []

        df = deepcopy(d1)

        # 处理原始数据中的NaN值
        df.fillna(0, inplace=True)

        data: List[BarData] = []
        if df is not None:
            if interval.value in ["d"]:
                data = self.handle_bar_data(df, symbol, exchange, interval, start, end)
            elif interval.value in ['w']:
                df.index = pd.DatetimeIndex(pd.to_datetime(df['date']))
                w_df = df.resample('W').agg(func_price_map).dropna()
                w_df.index = w_df.index + to_offset("-2D")
                dt = w_df.index.to_pydatetime()
                w_df["date"] = [x.date() for x in dt]
                data = self.handle_bar_data(w_df, symbol, exchange, interval, start, end)
        return data

    def handle_bar_data(self, df, symbol, exchange, interval, start, end):
        bar_dict: Dict[datetime, BarData] = {}
        data: List[BarData] = []

        adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

        for row in df.itertuples():
            dt: datetime = None
            if type(row.date) == Timestamp:
                dt = row.date.to_pydatetime() - adjustment
            elif type(row.date) == date:
                dt = row.date - adjustment
                dt = datetime.combine(dt, datetime.min.time())
            elif type(row.date) == str:
                dt = datetime.strptime(row.date, "%Y-%m-%d")

            if dt is None:
                continue

            dt = dt.replace(tzinfo=CHINA_TZ)

            if dt < start or dt > end:
                continue

            turnover = 0
            open_interest = 0

            bar: BarData = BarData(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime=dt,
                open_price=round_to(row.open, 0.000001),
                high_price=round_to(row.high, 0.000001),
                low_price=round_to(row.low, 0.000001),
                close_price=round_to(row.close, 0.000001),
                volume=row.volume,
                turnover=turnover,
                open_interest=open_interest,
                gateway_name="AK"
            )

            bar_dict[dt] = bar

        bar_keys = bar_dict.keys()
        bar_keys = sorted(bar_keys, reverse=False)
        for i in bar_keys:
            data.append(bar_dict[i])
        return data
