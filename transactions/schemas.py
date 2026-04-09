from datetime import datetime
from decimal import Decimal
from typing import Literal

from ninja import Schema


class TransactionBase(Schema):
    amount: Decimal
    date: datetime
    category: str
    type: Literal["income", "expense"]
    description: str = ""


class TransactionIn(TransactionBase):
    id: str


class TransactionOut(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime


class ErrorOut(Schema):
    message: str
