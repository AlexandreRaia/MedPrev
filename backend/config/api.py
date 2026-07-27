from typing import Literal

from django.conf import settings
from ninja import NinjaAPI, Schema

from apps.contas.admin_api import router as administracao_router
from apps.contas.api import router as contas_router
from apps.legado.api import router as legado_router


class HealthResponse(Schema):
    status: Literal["ok"]
    service: str


api = NinjaAPI(
    title="MedPrev API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)
api.add_router("/auth", contas_router)
api.add_router("/administracao", administracao_router)
api.add_router("/legado", legado_router)


@api.get(
    "/health",
    response=HealthResponse,
    tags=["Sistema"],
    summary="Verificar disponibilidade da API",
)
def health(request) -> HealthResponse:
    del request
    return HealthResponse(status="ok", service="medprev-api")
