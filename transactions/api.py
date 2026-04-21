from ninja import Query, Router

from .selectors import get_transactions_summary, list_transactions
from .services import (
    TransactionConflictError,
    create_financial_goal,
    create_transaction,
    delete_financial_goal,
    delete_transaction,
    list_financial_goals,
    sync_transactions,
    update_financial_goal,
    update_transaction,
)
from .schemas import (
    ErrorOut,
    FinancialGoalIn,
    FinancialGoalOut,
    FinancialGoalUpdateIn,
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
financial_goals_router = Router()


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


@financial_goals_router.get("/", response=list[FinancialGoalOut])
def list_financial_goals_endpoint(request):
    return list_financial_goals()


@financial_goals_router.post("/", response={201: FinancialGoalOut, 409: ErrorOut})
def create_financial_goal_endpoint(request, payload: FinancialGoalIn):
    try:
        goal = create_financial_goal(payload)
    except TransactionConflictError as exc:
        return 409, {
            "message": exc.message,
            "fields": exc.fields,
        }

    return 201, goal


@financial_goals_router.put("/{goal_id}", response=FinancialGoalOut)
def update_financial_goal_endpoint(
    request,
    goal_id: str,
    payload: FinancialGoalUpdateIn,
):
    return update_financial_goal(goal_id, payload)


@financial_goals_router.delete("/{goal_id}", response={204: None})
@financial_goals_router.delete(
    "/{goal_id}/",
    response={204: None},
    include_in_schema=False,
)
def delete_financial_goal_endpoint(request, goal_id: str):
    delete_financial_goal(goal_id)
    return 204, None
