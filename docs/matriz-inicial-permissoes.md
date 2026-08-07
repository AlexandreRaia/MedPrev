# Matriz inicial de usuários e permissões

Esta é a configuração inicial do MVP. Um administrador pode alterar as
permissões dos perfis pela tela Matriz de acesso. Cada usuário pertence
obrigatoriamente a uma única unidade. O perfil define as ações permitidas e a
unidade define o escopo padrão dos dados.

## Unidades

O sistema cria inicialmente:

- Administração;
- Medicina do Trabalho;
- Caixa de Previdência.

Secretarias individuais podem ser cadastradas como novas unidades. A
permissão `visualizar_dados_globais` concede visão transversal sem vincular o
usuário a várias unidades.

## Perfis

`Médico do Trabalho` e `Médico Perito` tinham exatamente as mesmas permissões —
a unidade do usuário (Medicina do Trabalho ou Caixa de Previdência) já
distinguia quem era quem. Os dois viraram um único perfil `Médico`. A vaga
liberada, mais três novas, formam a equipe de apoio multidisciplinar da
Medicina do Trabalho: `Enfermagem`, `Neuropsicólogo`, `Assistente Social` e
`Segurança do Trabalho`.

| Perfil | Consultar dados | Alterar administrativos | Consultar médico | Alterar médico | Gerenciar acessos | Visão global | Solicitar apoio | Responder apoio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Administrador | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Sim |
| Gestor da Administração | Sim | Não | Não | Não | Não | Sim | Não | Não |
| Operador Administrativo | Sim | Sim | Não | Não | Não | Não | Não | Não |
| Médico | Sim | Não | Sim | Sim | Não | Não | Sim | Não |
| Enfermagem | Sim | Não | Sim | Não | Não | Não | Não | Não |
| Neuropsicólogo | Não* | Não* | Não* | Não | Não | Não | Não | Sim |
| Assistente Social | Não* | Não* | Não* | Não | Não | Não | Não | Sim |
| Segurança do Trabalho | Não* | Não* | Não* | Não | Não | Não | Não | Sim |

\* Os três perfis de apoio não têm consulta geral ao cadastro — menor
privilégio. Eles só enxergam um servidor específico depois de receber uma
solicitação de apoio endereçada à sua especialidade (`responder_solicitacao_apoio`),
e a resposta que registram passa a integrar o histórico clínico do servidor,
visível a quem tem `consultar_conteudo_medico`.

O superusuário do Django é uma conta técnica e não representa um perfil de
negócio.

O perfil `Auditor` foi removido: não havia nenhuma tela ou API de auditoria
construída ainda para justificá-lo, e a permissão `visualizar_auditoria` foi
removida junto. Quando a trilha de auditoria (Marco 7) for priorizada, um
perfil dedicado pode voltar a ser criado com as permissões que fizerem
sentido na hora.

A Visão Geral (painel de indicadores) não depende mais de uma permissão
específica: os números que ela mostra são agregados e não identificam nenhum
servidor, então qualquer perfil autenticado a vê — do sistema inteiro, sem
escopo por unidade. A Consulta já permite localizar qualquer servidor
independente da unidade de quem procura, então restringir só o painel
agregado não protegia nada. Só o cartão pessoal de solicitações pendentes
continua específico do usuário, porque é sobre o que ele mesmo tem para
fazer.

## Permissões de negócio

| Código | Uso |
|---|---|
| `contas.gerenciar_acessos` | Administração de usuários, perfis e unidades |
| `contas.consultar_dados` | Consulta cadastral e administrativa |
| `contas.alterar_dados_administrativos` | Alterações administrativas |
| `contas.consultar_conteudo_medico` | Visualização de conteúdo médico |
| `contas.alterar_conteudo_medico` | Criação e alteração de conteúdo médico |
| `contas.visualizar_dados_globais` | Consulta dos dados de todas as unidades |
| `contas.solicitar_apoio_especializado` | Solicitar apoio de Neuropsicólogo, Assistente Social ou Segurança do Trabalho |
| `contas.responder_solicitacao_apoio` | Responder solicitações de apoio direcionadas à própria especialidade |

As rotas verificam a permissão específica no backend. Ocultar um botão no
frontend não substitui autorização. A permissão `gerenciar_acessos` permanece
obrigatória no perfil Administrador para evitar o bloqueio do painel.

## Autenticação e senha temporária

O MVP usa sessão Django com cookie `HttpOnly` e proteção CSRF:

1. `GET /api/v1/auth/csrf` cria o cookie e retorna o token;
2. `POST /api/v1/auth/login` inicia a sessão;
3. `GET /api/v1/auth/me` retorna usuário, unidade, perfil e permissões;
4. uma senha definida pelo administrador marca `deve_trocar_senha`;
5. `POST /api/v1/auth/alterar-senha` exige a senha atual e libera o acesso;
6. `POST /api/v1/auth/logout` encerra a sessão.

Usuário não autenticado recebe `401`. Usuário autenticado sem a permissão
necessária recebe `403`.

## Gestão e auditoria

A interface administrativa permite:

- listar, cadastrar e editar usuários;
- atribuir exatamente um perfil e uma unidade;
- ativar e desativar contas, sem exclusão física;
- redefinir senha temporária;
- listar, cadastrar e editar unidades;
- desativar e reativar unidades sem usuários ativos;
- consultar a matriz padronizada.
- configurar as permissões da matriz, com registro de auditoria.

São auditados login, falha de login, logout, criação e edição de usuários,
ativação, desativação, redefinição administrativa e alteração da própria senha.
Senhas e tokens nunca são armazenados nos eventos.

O sistema impede a autodesativação e preserva ao menos um Administrador ativo.
