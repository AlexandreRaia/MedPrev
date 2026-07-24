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

| Perfil | Consultar dados | Alterar administrativos | Consultar médico | Alterar médico | Gerenciar acessos | Ver auditoria | Visão global | Indicadores gerenciais |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Administrador | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Sim |
| Gestor da Administração | Sim | Não | Não | Não | Não | Não | Sim | Sim |
| Operador Administrativo | Sim | Sim | Não | Não | Não | Não | Não | Não |
| Médico do Trabalho | Sim | Não | Sim | Sim | Não | Não | Não | Não |
| Médico Perito | Sim | Não | Sim | Sim | Não | Não | Não | Não |
| Auditor | Sim | Não | Não | Não | Não | Sim | Não | Não |

O superusuário do Django é uma conta técnica e não representa um perfil de
negócio.

## Permissões de negócio

| Código | Uso |
|---|---|
| `contas.gerenciar_acessos` | Administração de usuários, perfis e unidades |
| `contas.consultar_dados` | Consulta cadastral e administrativa |
| `contas.alterar_dados_administrativos` | Alterações administrativas |
| `contas.consultar_conteudo_medico` | Visualização de conteúdo médico |
| `contas.alterar_conteudo_medico` | Criação e alteração de conteúdo médico |
| `contas.visualizar_auditoria` | Consulta à trilha de auditoria |
| `contas.visualizar_dados_globais` | Consulta dos dados de todas as unidades |
| `contas.visualizar_indicadores_gerenciais` | Acesso aos painéis gerenciais |

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
