from datetime import datetime
from decimal import Decimal

from ninja import Schema


class TransactionIn(Schema):
    id: str
    amount: Decimal
    date: datetime
    category: str
    type: str
    description: str = ""


class TransactionOut(Schema):
    id: str
    amount: Decimal
    date: datetime
    category: str
    type: str
    description: str
    created_at: datetime
    updated_at: datetime
