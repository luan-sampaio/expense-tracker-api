FIELD_MESSAGES = {
    "amount": "Informe o valor da transação.",
    "category": "Escolha uma categoria para a transação.",
    "date": "Informe uma data válida.",
    "description": "Informe uma descrição para a transação.",
    "id": "Informe o identificador da transação.",
    "limit": "Informe um limite válido.",
    "offset": "Informe um offset válido.",
    "operation": "Escolha uma operação válida.",
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


def get_validation_field(error, message):
    field = error.get("loc", [""])[-1]
    if field in FIELD_MESSAGES:
        return field

    if "categoria" in message:
        return "category"

    if "mês" in message:
        return "month"

    if "limite" in message:
        return "limit"

    return "non_field_errors"


def validation_fields_from_errors(errors):
    fields = {}
    for error in errors:
        message = get_validation_message(error)
        fields[get_validation_field(error, message)] = message
    return fields
