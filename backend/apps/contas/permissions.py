GERENCIAR_ACESSOS = "gerenciar_acessos"
CONSULTAR_DADOS = "consultar_dados"
ALTERAR_DADOS_ADMINISTRATIVOS = "alterar_dados_administrativos"
CONSULTAR_CONTEUDO_MEDICO = "consultar_conteudo_medico"
ALTERAR_CONTEUDO_MEDICO = "alterar_conteudo_medico"
VISUALIZAR_DADOS_GLOBAIS = "visualizar_dados_globais"
SOLICITAR_APOIO_ESPECIALIZADO = "solicitar_apoio_especializado"
RESPONDER_SOLICITACAO_APOIO = "responder_solicitacao_apoio"

PERMISSOES_DE_NEGOCIO = (
    (GERENCIAR_ACESSOS, "Pode gerenciar usuários, grupos e permissões"),
    (CONSULTAR_DADOS, "Pode consultar dados cadastrais e administrativos"),
    (
        ALTERAR_DADOS_ADMINISTRATIVOS,
        "Pode alterar dados administrativos",
    ),
    (CONSULTAR_CONTEUDO_MEDICO, "Pode consultar conteúdo médico"),
    (ALTERAR_CONTEUDO_MEDICO, "Pode criar e alterar conteúdo médico"),
    (
        VISUALIZAR_DADOS_GLOBAIS,
        "Pode visualizar dados de todas as unidades",
    ),
    (
        SOLICITAR_APOIO_ESPECIALIZADO,
        "Pode solicitar apoio de especialista (Neuropsicólogo, Assistente "
        "Social, Segurança do Trabalho)",
    ),
    (
        RESPONDER_SOLICITACAO_APOIO,
        "Pode responder solicitações de apoio direcionadas à sua especialidade",
    ),
)

PERFIS_E_PERMISSOES = {
    "Administrador": tuple(codename for codename, _ in PERMISSOES_DE_NEGOCIO),
    "Gestor da Administração": (
        CONSULTAR_DADOS,
        VISUALIZAR_DADOS_GLOBAIS,
    ),
    "Operador Administrativo": (
        CONSULTAR_DADOS,
        ALTERAR_DADOS_ADMINISTRATIVOS,
    ),
    "Médico": (
        CONSULTAR_DADOS,
        CONSULTAR_CONTEUDO_MEDICO,
        ALTERAR_CONTEUDO_MEDICO,
        SOLICITAR_APOIO_ESPECIALIZADO,
    ),
    "Enfermagem": (
        CONSULTAR_DADOS,
        CONSULTAR_CONTEUDO_MEDICO,
    ),
    "Neuropsicólogo": (RESPONDER_SOLICITACAO_APOIO,),
    "Assistente Social": (RESPONDER_SOLICITACAO_APOIO,),
    "Segurança do Trabalho": (RESPONDER_SOLICITACAO_APOIO,),
}


def nome_completo_da_permissao(codename: str) -> str:
    return f"contas.{codename}"
