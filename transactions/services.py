import hashlib
import json

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError

from .models import FinancialGoal, SyncOperationLog, Transaction
from .schemas import TransactionIn
from .validation import validation_fields_from_errors


class TransactionConflictError(Exception):
    def __init__(self, message, fields):
        self.message = message
        self.fields = fields
        super().__init__(message)


def transaction_values_from_payload(payload, exclude=None):
    values = payload.model_dump(exclude=exclude or set())
    values["financial_nature"] = values.pop("financialNature")
    values["budget_group_id"] = values.pop("budgetGroupId")
    values["goal_id"] = values.pop("goalId")
    return values


def create_transaction(payload):
    if Transaction.objects.filter(id=payload.id).exists():
        raise TransactionConflictError(
            "Não foi possível salvar a transação.",
            {"id": "Já existe uma transação com este identificador."},
        )

    return Transaction.objects.create(
        id=payload.id,
        **transaction_values_from_payload(payload, exclude={"id"}),
    )


def update_transaction(transaction_id, payload):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    for field, value in transaction_values_from_payload(payload, exclude={"id"}).items():
        setattr(transaction, field, value)
    transaction.save()
    return transaction


def delete_transaction(transaction_id):
    Transaction.objects.filter(id=transaction_id).delete()


def operation_payload_hash(operation):
    payload = operation.model_dump(mode="json")
    encoded_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def build_sync_result(
    operation,
    transaction_id,
    status,
    message,
    server_synced_at,
    fields=None,
):
    return {
        "operation": operation.operation,
        "transaction_id": transaction_id,
        "client_operation_id": operation.client_operation_id,
        "status": status,
        "message": message,
        "fields": fields or {},
        "server_synced_at": server_synced_at,
    }


def result_from_log(operation, log, payload_hash):
    message = log.message
    status = log.status

    if log.payload_hash != payload_hash:
        status = SyncOperationLog.Status.FAILED
        message = "Este client_operation_id já foi usado com outros dados."
    elif not message and log.status == SyncOperationLog.Status.APPLIED:
        message = "Operação já sincronizada anteriormente."

    return build_sync_result(
        operation,
        log.transaction_id or None,
        status,
        message,
        log.server_synced_at,
        log.fields,
    )


def save_operation_log(operation, transaction_id, payload_hash, result):
    if not operation.client_operation_id:
        return None

    log = SyncOperationLog.objects.create(
        client_operation_id=operation.client_operation_id,
        operation=operation.operation,
        transaction_id=transaction_id or "",
        payload_hash=payload_hash,
        status=result["status"],
        message=result["message"],
        fields=result["fields"],
    )
    result["server_synced_at"] = log.server_synced_at
    return log


def sync_transactions(payload):
    results = []
    server_synced_at = timezone.now()

    with db_transaction.atomic():
        for operation in payload.operations:
            transaction_id = operation.transaction_id
            if operation.transaction:
                transaction_id = operation.transaction.get("id") or transaction_id

            payload_hash = operation_payload_hash(operation)
            if operation.client_operation_id:
                log = SyncOperationLog.objects.filter(
                    client_operation_id=operation.client_operation_id
                ).first()
                if log:
                    results.append(result_from_log(operation, log, payload_hash))
                    continue

            result = build_sync_result(
                operation,
                transaction_id,
                SyncOperationLog.Status.APPLIED,
                "",
                server_synced_at,
            )

            if operation.operation not in {"add", "update", "remove"}:
                result["status"] = SyncOperationLog.Status.FAILED
                result["message"] = "Escolha uma operação válida."
                result["fields"] = {"operation": result["message"]}
                save_operation_log(operation, transaction_id, payload_hash, result)
                results.append(result)
                continue

            if operation.operation in {"add", "update"}:
                if operation.transaction is None:
                    result["status"] = SyncOperationLog.Status.FAILED
                    result["message"] = (
                        "Informe os dados da transação para adicionar ou atualizar."
                    )
                    result["fields"] = {"transaction": result["message"]}
                    save_operation_log(operation, transaction_id, payload_hash, result)
                    results.append(result)
                    continue

                try:
                    transaction_payload = TransactionIn.model_validate(
                        operation.transaction
                    )
                except PydanticValidationError as exc:
                    result["status"] = SyncOperationLog.Status.FAILED
                    result["fields"] = validation_fields_from_errors(
                        exc.errors(include_url=False)
                    )
                    result["message"] = "Revise os campos destacados."
                    save_operation_log(operation, transaction_id, payload_hash, result)
                    results.append(result)
                    continue

                transaction_id = transaction_payload.id
                result["transaction_id"] = transaction_id
                values = transaction_values_from_payload(
                    transaction_payload,
                    exclude={"id"},
                )
                Transaction.objects.update_or_create(
                    id=transaction_payload.id,
                    defaults=values,
                )

            if operation.operation == "remove":
                if not transaction_id:
                    result["status"] = SyncOperationLog.Status.FAILED
                    result["message"] = (
                        "Informe o identificador da transação para remover."
                    )
                    result["fields"] = {"transaction_id": result["message"]}
                    save_operation_log(operation, transaction_id, payload_hash, result)
                    results.append(result)
                    continue

                Transaction.objects.filter(id=transaction_id).delete()

            save_operation_log(operation, transaction_id, payload_hash, result)
            results.append(result)

    return {
        "results": results,
        "transactions": Transaction.objects.all(),
        "server_synced_at": server_synced_at,
    }


def financial_goal_values_from_payload(payload, exclude=None, exclude_none=False):
    values = payload.model_dump(exclude=exclude or set(), exclude_none=exclude_none)
    if "targetAmount" in values:
        values["target_amount"] = values.pop("targetAmount")
    if "createdAt" in values:
        values["created_at"] = values.pop("createdAt")
    if "isArchived" in values:
        values["is_archived"] = values.pop("isArchived")

    if values.get("created_at") is None:
        values.pop("created_at", None)

    return values


def list_financial_goals():
    return FinancialGoal.objects.all()


def create_financial_goal(payload):
    if FinancialGoal.objects.filter(id=payload.id).exists():
        raise TransactionConflictError(
            "Não foi possível salvar a meta financeira.",
            {"id": "Já existe uma meta financeira com este identificador."},
        )

    return FinancialGoal.objects.create(
        id=payload.id,
        **financial_goal_values_from_payload(
            payload,
            exclude={"id"},
            exclude_none=True,
        ),
    )


def update_financial_goal(goal_id, payload):
    goal = get_object_or_404(FinancialGoal, id=goal_id)
    for field, value in financial_goal_values_from_payload(
        payload,
        exclude_none=True,
    ).items():
        setattr(goal, field, value)
    goal.save()
    return goal


def delete_financial_goal(goal_id):
    FinancialGoal.objects.filter(id=goal_id).delete()
