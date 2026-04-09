from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Transaction
from .schemas import TransactionIn, TransactionOut

router = Router()


@router.get("/", response=list[TransactionOut])
def list_transactions(request):
    return Transaction.objects.all()


@router.post("/", response=TransactionOut)
def upsert_transaction(request, payload: TransactionIn):
    transaction, _ = Transaction.objects.update_or_create(
        id=payload.id,
        defaults={
            "amount": payload.amount,
            "date": payload.date,
            "category": payload.category,
            "type": payload.type,
            "description": payload.description,
        },
    )
    return transaction


@router.put("/{transaction_id}", response=TransactionOut)
def update_transaction(request, transaction_id: str, payload: TransactionIn):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    for field, value in payload.dict(exclude={"id"}).items():
        setattr(transaction, field, value)
    transaction.save()
    return transaction


@router.delete("/{transaction_id}", response={204: None})
def delete_transaction(request, transaction_id: str):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    transaction.delete()
    return 204, None
