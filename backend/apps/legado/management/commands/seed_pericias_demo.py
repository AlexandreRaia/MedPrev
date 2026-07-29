import datetime

from django.core.management.base import BaseCommand

from apps.legado.models import Pericia, Protocolo, ProtocoloCid

SERVIDOR_DEMONSTRACAO = 1001
PROTOCOLO_ORIGINAL_DO_DUMP = 1
PERICIA_ORIGINAL_DO_DUMP = 1

# Faixa de códigos reservada só para este comando. Bem acima de qualquer id
# real do dump (protocolo vai até 30, pericia e protocolocid até 10), então
# nunca colide com dado importado de verdade.
ID_BASE_DEMO = 9000

PERICIAS_DEMO = (
    {
        "dias_atras": 5,
        "cid": "Z09",
        "situacao": 1,
        "ds_subjetivo": "Retorno de acompanhamento.",
        "ds_objetivo": "Paciente relata melhora significativa.",
        "ds_conduta": "Alta do acompanhamento.",
        "ic_atestado": None,
        "qt_atestadodias": None,
    },
    {
        "dias_atras": 18,
        "cid": "M54.5",
        "situacao": 3,
        "ds_subjetivo": "Dor lombar recorrente.",
        "ds_objetivo": "Exame osteomuscular alterado.",
        "ds_conduta": "Encaminhado para fisioterapia.",
        "ic_atestado": "t",
        "qt_atestadodias": 5,
    },
    {
        "dias_atras": 40,
        "cid": "R50.9",
        "situacao": 3,
        "ds_subjetivo": "Episódio febril.",
        "ds_objetivo": "Temperatura elevada, demais parâmetros normais.",
        "ds_conduta": "Repouso e hidratação.",
        "ic_atestado": "t",
        "qt_atestadodias": 3,
    },
    {
        "dias_atras": 75,
        "cid": "Z02.9",
        "situacao": 3,
        "ds_subjetivo": "Consulta de rotina.",
        "ds_objetivo": "Sem alterações relevantes.",
        "ds_conduta": "Manter acompanhamento habitual.",
        "ic_atestado": None,
        "qt_atestadodias": None,
    },
    {
        "dias_atras": 130,
        "cid": "M79.1",
        "situacao": 3,
        "ds_subjetivo": "Lombalgia aguda.",
        "ds_objetivo": "Limitação leve de movimento.",
        "ds_conduta": "Encaminhado para fisioterapia.",
        "ic_atestado": "t",
        "qt_atestadodias": 7,
    },
)


class Command(BaseCommand):
    help = (
        "Recria protocolos, CIDs e perícias fictícias extras do Servidor "
        "Teste 01, cada perícia com seu próprio protocolo e código de CID "
        "(datas relativas à data atual, algumas dentro e outras fora da "
        "janela de 60 dias). Não faz parte do sismed.dump oficial (o "
        "protocolo/perícia originais do dump, id=1, nunca são alterados). "
        "Seguro rodar quantas vezes for preciso: sempre substitui o dado de "
        "demonstração anterior pelo novo."
    )

    def handle(self, *args, **options) -> None:
        del args, options

        Pericia.objects.filter(cd_pericia__gte=ID_BASE_DEMO).delete()
        ProtocoloCid.objects.filter(cd_protocolocid__gte=ID_BASE_DEMO).delete()
        removidos, _ = Protocolo.objects.filter(cd_protocolo__gte=ID_BASE_DEMO).delete()

        hoje = datetime.date.today()
        for indice, dados in enumerate(PERICIAS_DEMO):
            novo_id = ID_BASE_DEMO + indice
            data = hoje - datetime.timedelta(days=dados["dias_atras"])

            Protocolo.objects.create(
                cd_protocolo=novo_id,
                dt_protocolo=data,
                cd_servidor=SERVIDOR_DEMONSTRACAO,
                cd_situacaoprotocolo=dados["situacao"],
            )
            ProtocoloCid.objects.create(
                cd_protocolocid=novo_id,
                cd_protocolo=novo_id,
                cd_cid=dados["cid"],
                st_ativo=True,
            )
            Pericia.objects.create(
                cd_pericia=novo_id,
                cd_protocolo=novo_id,
                dt_pericia=data,
                ds_subjetivo=dados["ds_subjetivo"],
                ds_objetivo=dados["ds_objetivo"],
                ds_conduta=dados["ds_conduta"],
                ic_atestado=dados["ic_atestado"],
                qt_atestadodias=dados["qt_atestadodias"],
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{removidos} protocolo(s) de demonstração antigo(s) removido(s); "
                f"{len(PERICIAS_DEMO)} novo(s) protocolo/CID/perícia criados para "
                "o Servidor Teste 01."
            )
        )
