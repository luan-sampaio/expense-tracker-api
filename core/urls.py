from django.urls import path
from ninja import NinjaAPI
from ninja.errors import ValidationError

from transactions.api import router as transactions_router

api = NinjaAPI(title="Track Book API", version="1.0.0", docs_url="/docs")

api.add_router("/transactions", transactions_router)


FIELD_MESSAGES = {
    "amount": "Informe o valor da transação.",
    "category": "Escolha uma categoria para a transação.",
    "date": "Informe uma data válida.",
    "description": "Informe uma descrição para a transação.",
    "id": "Informe o identificador da transação.",
    "transaction": "Informe os dados da transação.",
    "transaction_id": "Informe o identificador da transação.",
    "type": "Escolha o tipo da transação.",
}

TYPE_MESSAGES = {
    "decimal_parsing": "Informe um valor válido.",
    "decimal_type": "Informe um valor válido.",
    "datetime_from_date_parsing": "Informe uma data válida.",
    "datetime_parsing": "Informe uma data válida.",
    "datetime_type": "Informe uma data válida.",
    "literal_error": "Escolha uma opção válida.",
}


def get_validation_message(error):
    field = error.get("loc", [""])[-1]
    if error.get("type") in {"missing", "string_type"}:
        return FIELD_MESSAGES.get(field, "Preencha este campo.")

    if error.get("type") == "literal_error" and field in FIELD_MESSAGES:
        return FIELD_MESSAGES[field]

    if error.get("type") in TYPE_MESSAGES:
        return TYPE_MESSAGES[error["type"]]

    ctx_error = error.get("ctx", {}).get("error")
    if ctx_error:
        return str(ctx_error)

    return error.get("msg", "Revise os dados enviados.")


@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    errors = [
        {
            "field": error.get("loc", [""])[-1],
            "message": get_validation_message(error),
        }
        for error in exc.errors
    ]
    message = (
        errors[0]["message"]
        if len(errors) == 1
        else "Alguns campos precisam ser corrigidos."
    )
    return api.create_response(
        request,
        {
            "message": message,
            "errors": errors,
        },
        status=422,
    )


urlpatterns = [
    path("api/", api.urls),
]
