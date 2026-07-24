from typing import Literal

from django.conf import settings
from ninja import NinjaAPI, Schema


class HealthResponse(Schema):
    status: Literal["ok"]
    service: str


api = NinjaAPI(
    title="MedPrev API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)


@api.get(
    "/health",
    response=HealthResponse,
    tags=["Sistema"],
    summary="Verificar disponibilidade da API",
)
def health(request) -> HealthResponse:
    del request
    return HealthResponse(status="ok", service="medprev-api")
