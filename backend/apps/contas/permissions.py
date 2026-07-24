GERENCIAR_ACESSOS = "gerenciar_acessos"
CONSULTAR_DADOS = "consultar_dados"
ALTERAR_DADOS_ADMINISTRATIVOS = "alterar_dados_administrativos"
CONSULTAR_CONTEUDO_MEDICO = "consultar_conteudo_medico"
ALTERAR_CONTEUDO_MEDICO = "alterar_conteudo_medico"
VISUALIZAR_AUDITORIA = "visualizar_auditoria"
VISUALIZAR_DADOS_GLOBAIS = "visualizar_dados_globais"
VISUALIZAR_INDICADORES_GERENCIAIS = "visualizar_indicadores_gerenciais"

PERMISSOES_DE_NEGOCIO = (
    (GERENCIAR_ACESSOS, "Pode gerenciar usuários, grupos e permissões"),
    (CONSULTAR_DADOS, "Pode consultar dados cadastrais e administrativos"),
    (
        ALTERAR_DADOS_ADMINISTRATIVOS,
        "Pode alterar dados administrativos",
    ),
    (CONSULTAR_CONTEUDO_MEDICO, "Pode consultar conteúdo médico"),
    (ALTERAR_CONTEUDO_MEDICO, "Pode criar e alterar conteúdo médico"),
    (VISUALIZAR_AUDITORIA, "Pode visualizar a auditoria"),
    (
        VISUALIZAR_DADOS_GLOBAIS,
        "Pode visualizar dados de todas as unidades",
    ),
    (
        VISUALIZAR_INDICADORES_GERENCIAIS,
        "Pode visualizar indicadores gerenciais",
    ),
)

PERFIS_E_PERMISSOES = {
    "Administrador": tuple(codename for codename, _ in PERMISSOES_DE_NEGOCIO),
    "Gestor da Administração": (
        CONSULTAR_DADOS,
        VISUALIZAR_DADOS_GLOBAIS,
        VISUALIZAR_INDICADORES_GERENCIAIS,
    ),
    "Operador Administrativo": (
        CONSULTAR_DADOS,
        ALTERAR_DADOS_ADMINISTRATIVOS,
    ),
    "Médico do Trabalho": (
        CONSULTAR_DADOS,
        CONSULTAR_CONTEUDO_MEDICO,
        ALTERAR_CONTEUDO_MEDICO,
    ),
    "Médico Perito": (
        CONSULTAR_DADOS,
        CONSULTAR_CONTEUDO_MEDICO,
        ALTERAR_CONTEUDO_MEDICO,
    ),
    "Auditor": (
        CONSULTAR_DADOS,
        VISUALIZAR_AUDITORIA,
    ),
}


def nome_completo_da_permissao(codename: str) -> str:
    return f"contas.{codename}"
