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


class TransactionSyncOperationIn(Schema):
    operation: Literal["add", "update", "remove"]
    transaction: TransactionIn | None = None
    transaction_id: str | None = None
    client_operation_id: str | None = None


class TransactionSyncIn(Schema):
    operations: list[TransactionSyncOperationIn]


class TransactionSyncOperationOut(Schema):
    operation: Literal["add", "update", "remove"]
    transaction_id: str | None = None
    client_operation_id: str | None = None
    status: Literal["applied", "failed"]
    message: str = ""


class TransactionSyncOut(Schema):
    results: list[TransactionSyncOperationOut]
    transactions: list[TransactionOut]
