from ninja import Query, Router

from .selectors import get_transactions_summary, list_transactions
from .services import (
    TransactionConflictError,
    create_transaction,
    delete_transaction,
    sync_transactions,
    update_transaction,
)
from .schemas import (
    ErrorOut,
    MonthFilter,
    TransactionFilters,
    TransactionIn,
    TransactionListOut,
    TransactionOut,
    TransactionSummaryOut,
    TransactionSyncIn,
    TransactionSyncOut,
)

router = Router()


@router.get("/", response=TransactionListOut)
def list_transactions_endpoint(request, filters: Query[TransactionFilters]):
    return list_transactions(filters)


@router.get("/summary", response=TransactionSummaryOut)
def get_transactions_summary_endpoint(request, filters: Query[MonthFilter]):
    return get_transactions_summary(filters)


@router.post("/", response={201: TransactionOut, 409: ErrorOut})
def create_transaction_endpoint(request, payload: TransactionIn):
    try:
        transaction = create_transaction(payload)
    except TransactionConflictError as exc:
        return 409, {
            "message": exc.message,
            "fields": exc.fields,
        }

    return 201, transaction


@router.post("/sync", response=TransactionSyncOut)
def sync_transactions_endpoint(request, payload: TransactionSyncIn):
    return sync_transactions(payload)


@router.put("/{transaction_id}", response=TransactionOut)
def update_transaction_endpoint(request, transaction_id: str, payload: TransactionIn):
    return update_transaction(transaction_id, payload)


@router.delete("/{transaction_id}", response={204: None})
@router.delete("/{transaction_id}/", response={204: None}, include_in_schema=False)
def delete_transaction_endpoint(request, transaction_id: str):
    delete_transaction(transaction_id)
    return 204, None
