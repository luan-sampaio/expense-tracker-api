from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Transaction
from .schemas import ErrorOut, TransactionIn, TransactionOut

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
