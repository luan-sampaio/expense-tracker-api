from datetime import datetime
from decimal import Decimal
from typing import Literal

from ninja import Schema
from pydantic import field_validator, model_validator


MAX_DESCRIPTION_LENGTH = 255

EXPENSE_CATEGORIES = {
    "food",
    "transport",
    "housing",
    "entertainment",
    "health",
    "education",
    "shopping",
    "bills",
    "other",
}
INCOME_CATEGORIES = {
    "salary",
    "freelance",
    "investment",
    "gift",
    "other",
}
ACCEPTED_CATEGORIES = EXPENSE_CATEGORIES | INCOME_CATEGORIES
ACCEPTED_CATEGORIES_BY_TYPE = {
    "expense": EXPENSE_CATEGORIES,
    "income": INCOME_CATEGORIES,
}


class TransactionBase(Schema):
    amount: Decimal
    date: datetime
    category: str
    type: Literal["income", "expense"]
    description: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, amount):
        if amount <= Decimal("0"):
            raise ValueError("O valor da transação deve ser maior que zero.")
        return amount

    @field_validator("category")
    @classmethod
    def validate_category(cls, category):
        category = category.strip().lower()
        if not category:
            raise ValueError("Escolha uma categoria para a transação.")
        if category not in ACCEPTED_CATEGORIES:
            raise ValueError("Escolha uma categoria válida.")
        return category

    @field_validator("description")
    @classmethod
    def validate_description(cls, description):
        description = description.strip()
        if not description:
            raise ValueError("Informe uma descrição para a transação.")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"A descrição deve ter no máximo {MAX_DESCRIPTION_LENGTH} caracteres."
            )
        return description

    @model_validator(mode="after")
    def validate_category_matches_type(self):
        categories = ACCEPTED_CATEGORIES_BY_TYPE.get(self.type, set())
        if self.category not in categories:
            raise ValueError("A categoria escolhida não combina com o tipo da transação.")
        return self


class TransactionIn(TransactionBase):
    id: str


class TransactionOut(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime


class ErrorOut(Schema):
    message: str
    fields: dict[str, str] = {}


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
