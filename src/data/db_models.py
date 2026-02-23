"""
数据库 ORM 模型定义

使用 Peewee ORM 定义数据库表结构
"""
import peewee
from datetime import datetime

# 创建数据库连接
database = peewee.SqliteDatabase(None)


class BaseModel(peewee.Model):
    """基础模型类"""
    class Meta:
        database = database


class StockData(BaseModel):
    """股票日线数据模型"""
    symbol = peewee.CharField(max_length=20)
    date = peewee.DateField()
    open = peewee.FloatField()
    high = peewee.FloatField()
    low = peewee.FloatField()
    close = peewee.FloatField()
    volume = peewee.BigIntegerField()
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = database
        indexes = (
            (('symbol', 'date'), True),  # 联合唯一索引
        )


class SignalRecord(BaseModel):
    """交易信号记录模型"""
    signal_id = peewee.CharField(max_length=50, primary_key=True)
    symbol = peewee.CharField(max_length=20)
    signal_type = peewee.CharField(max_length=50)
    signal_time = peewee.DateTimeField()
    entry_price = peewee.FloatField()
    stop_loss = peewee.FloatField()
    target_price = peewee.FloatField()
    risk_reward_ratio = peewee.FloatField()
    confidence = peewee.FloatField()
    indicators = peewee.TextField()  # JSON 字符串
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = database


class OrderRecord(BaseModel):
    """订单记录模型"""
    order_id = peewee.CharField(max_length=50, primary_key=True)
    symbol = peewee.CharField(max_length=20)
    side = peewee.CharField(max_length=10)  # buy / sell
    order_type = peewee.CharField(max_length=20)  # limit / market / stop_limit
    quantity = peewee.IntegerField()
    price = peewee.FloatField()
    stop_price = peewee.FloatField(null=True)  # 止损价（可选）
    status = peewee.CharField(max_length=20)  # pending / filled / cancelled / rejected
    created_time = peewee.DateTimeField()
    updated_time = peewee.DateTimeField()
    filled_price = peewee.FloatField(null=True)
    filled_quantity = peewee.IntegerField(default=0)
    signal_id = peewee.CharField(max_length=50, null=True)  # 关联信号 ID

    class Meta:
        database = database


class PositionRecord(BaseModel):
    """持仓记录模型"""
    position_id = peewee.CharField(max_length=50, primary_key=True)
    symbol = peewee.CharField(max_length=20)
    entry_price = peewee.FloatField()
    current_price = peewee.FloatField()
    quantity = peewee.IntegerField()
    stop_loss = peewee.FloatField()
    target_price = peewee.FloatField()
    status = peewee.CharField(max_length=20)  # open / closed
    entry_time = peewee.DateTimeField()
    exit_time = peewee.DateTimeField(null=True)
    exit_price = peewee.FloatField(null=True)
    unrealized_pnl = peewee.FloatField()
    realized_pnl = peewee.FloatField()
    signal_id = peewee.CharField(max_length=50, null=True)  # 关联信号 ID

    class Meta:
        database = database
