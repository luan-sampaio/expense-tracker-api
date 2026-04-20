from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Transaction
from .schemas import (
    ErrorOut,
    TransactionIn,
    TransactionOut,
    TransactionSyncIn,
    TransactionSyncOut,
)

router = Router()


@router.get("/", response=list[TransactionOut])
def list_transactions(request):
    return Transaction.objects.all()


@router.post("/", response={201: TransactionOut, 409: ErrorOut})
def create_transaction(request, payload: TransactionIn):
    if Transaction.objects.filter(id=payload.id).exists():
        return 409, {"message": "Transaction with this id already exists."}

    transaction = Transaction.objects.create(
        id=payload.id,
        amount=payload.amount,
        date=payload.date,
        category=payload.category,
        type=payload.type,
        description=payload.description,
    )
    return 201, transaction


@router.post("/sync", response=TransactionSyncOut)
def sync_transactions(request, payload: TransactionSyncIn):
    results = []

    with db_transaction.atomic():
        for operation in payload.operations:
            transaction_id = operation.transaction_id
            if operation.transaction:
                transaction_id = operation.transaction.id

            result = {
                "operation": operation.operation,
                "transaction_id": transaction_id,
                "client_operation_id": operation.client_operation_id,
                "status": "applied",
                "message": "",
            }

            if operation.operation in {"add", "update"}:
                if operation.transaction is None:
                    result["status"] = "failed"
                    result["message"] = "Transaction payload is required for add/update operations."
                    results.append(result)
                    continue

                values = operation.transaction.model_dump(exclude={"id"})
                Transaction.objects.update_or_create(
                    id=operation.transaction.id,
                    defaults=values,
                )

            if operation.operation == "remove":
                if not transaction_id:
                    result["status"] = "failed"
                    result["message"] = "transaction_id is required for remove operations."
                    results.append(result)
                    continue

                Transaction.objects.filter(id=transaction_id).delete()

            results.append(result)

    return {
        "results": results,
        "transactions": Transaction.objects.all(),
    }


@router.put("/{transaction_id}", response=TransactionOut)
def update_transaction(request, transaction_id: str, payload: TransactionIn):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    for field, value in payload.model_dump(exclude={"id"}).items():
        setattr(transaction, field, value)
    transaction.save()
    return transaction


@router.delete("/{transaction_id}", response={204: None})
def delete_transaction(request, transaction_id: str):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.delete()
    return 204, None
