from django.urls import path
from ninja import NinjaAPI

from transactions.api import router as transactions_router

api = NinjaAPI(title="Track Book API", version="1.0.0", docs_url="/docs")

api.add_router("/transactions", transactions_router)

urlpatterns = [
    path("api/", api.urls),
]
