from django.urls import path
from ninja import NinjaAPI
from ninja.errors import ValidationError

from transactions.api import financial_goals_router, router as transactions_router
from transactions.validation import validation_fields_from_errors

api = NinjaAPI(title="Track Book API", version="1.0.0", docs_url="/docs")

api.add_router("/transactions", transactions_router)
api.add_router("/financial-goals", financial_goals_router)


@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    return api.create_response(
        request,
        {
            "message": "Revise os campos destacados.",
            "fields": validation_fields_from_errors(exc.errors),
        },
        status=422,
    )


urlpatterns = [
    path("api/", api.urls),
]
