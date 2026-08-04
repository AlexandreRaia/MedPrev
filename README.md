# MedPrev

Base full-stack do MedPrev, organizada como um monólito modular:

- Django e Django Ninja no backend;
- React com TypeScript no frontend;
- SQLite como banco único do ambiente local;
- PostgreSQL como destino futuro.

Durante o desenvolvimento não há conexão com o SisMed institucional. A
estrutura e os dados fictícios de `sismed.dump` são copiados para o mesmo
`backend/db.sqlite3` usado pelo Django, com leitura e escrita habilitadas.

## Pré-requisitos

- Python 3.12 ou superior;
- Node.js 20.19 ou superior;
- Docker com Docker Compose somente quando o PostgreSQL for habilitado.

## Preparar o ambiente

Na raiz do projeto, crie a configuração local:

```bash
cp .env.example .env
```

No Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Prepare o backend:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py migrate
```

## Importar os dados fictícios

Coloque `sismed.dump` na raiz do repositório e execute:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py importar_dados_ficticios
```

O comando:

- preserva as tabelas próprias do Django;
- cria as 92 tabelas contidas no dump no mesmo `db.sqlite3`;
- importa os 453 registros fictícios;
- converte tipos, valores padrão, chaves primárias e chaves estrangeiras;
- verifica a integridade referencial depois da importação.

Se as tabelas já tiverem sido importadas e for necessário voltar aos dados
originais do dump:

```powershell
.\.venv\Scripts\python.exe manage.py importar_dados_ficticios --replace
```

`--replace` apaga e recria somente as 92 tabelas originadas do dump. As tabelas
do Django, como usuários, sessões e migrations, são preservadas.

O dump e o `db.sqlite3` são artefatos locais e não são enviados ao GitHub.

## Iniciar os servidores

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py runserver
```

Frontend, em outro terminal:

```powershell
cd frontend
npm ci
npm run dev
```

A aplicação fica em <http://localhost:5173>, o teste da API em
<http://localhost:8000/api/v1/health> e a documentação OpenAPI em
<http://localhost:8000/api/v1/docs>.

## Acesso às tabelas importadas

Os primeiros modelos estão em `backend/apps/legado/models.py`:

- `Servidor`;
- `Protocolo`;
- `SituacaoProtocolo`;
- `Licenca`;
- `Pericia`.

Eles usam o banco `default`, permitem leitura e escrita e apontam diretamente
para as tabelas importadas. Os demais modelos serão acrescentados conforme cada
fluxo do produto for desenvolvido. O inventário completo está em
[`docs/dicionario-dados-sismed.md`](docs/dicionario-dados-sismed.md).

## Autenticação e permissões

O backend usa sessão Django, CSRF, grupos e permissões por ação de negócio.
Cada usuário pertence obrigatoriamente a uma única unidade. O perfil define o
que ele pode fazer; a unidade define o escopo padrão dos dados. A permissão
`visualizar_dados_globais` é a exceção explícita para perfis gestores.

A matriz do MVP possui os perfis Administrador, Gestor da Administração,
Operador Administrativo, Médico, Enfermagem, Neuropsicólogo, Assistente Social
e Segurança do Trabalho.

Endpoints:

- `GET /api/v1/auth/csrf`;
- `POST /api/v1/auth/login`;
- `POST /api/v1/auth/logout`;
- `GET /api/v1/auth/me`;
- `POST /api/v1/auth/alterar-senha`;
- `GET /api/v1/auth/matriz` — exclusivo para quem possui
  `contas.gerenciar_acessos`.
- `/api/v1/administracao/usuarios` — consulta, cadastro e edição;
- `/api/v1/administracao/usuarios/{id}/ativar`;
- `/api/v1/administracao/usuarios/{id}/desativar`;
- `/api/v1/administracao/usuarios/{id}/redefinir-senha`;
- `/api/v1/administracao/unidades` — consulta e cadastro;
- `/api/v1/administracao/unidades/{id}` — edição;
- `/api/v1/administracao/unidades/{id}/ativar`;
- `/api/v1/administracao/unidades/{id}/desativar`.

A matriz completa e o fluxo para o frontend estão em
[`docs/matriz-inicial-permissoes.md`](docs/matriz-inicial-permissoes.md).

Para criar a primeira conta técnica:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Depois, a própria interface do MedPrev permite cadastrar usuários, unidades,
perfis e senhas temporárias. O Django Admin permanece disponível como recurso
técnico. Não defina senhas padrão compartilhadas.

### Fluxo do frontend

Ao abrir <http://127.0.0.1:5173>, o React consulta a sessão atual:

- sem sessão, apresenta a tela de login;
- com sessão válida, apresenta o painel principal;
- depois do login, carrega nome, perfil e permissões;
- usuários com senha temporária precisam criar uma senha pessoal;
- administradores acessam usuários, unidades e configuram a matriz de
  permissões pelo menu lateral;
- ao sair, encerra a sessão no backend e retorna ao login.

O frontend solicita um token CSRF antes de login e logout. As decisões de
autorização continuam sendo verificadas pelo backend.

## Migração futura para PostgreSQL

O SQLite é temporário. O dump original já possui estrutura PostgreSQL, e a
migração definitiva será planejada quando o servidor estiver disponível.
Enquanto isso:

- regras de negócio não devem depender de comportamento exclusivo do SQLite;
- migrations próprias do MedPrev devem continuar compatíveis com PostgreSQL;
- relações ausentes no dump não devem ser inventadas;
- o dump deve ser tratado somente como massa fictícia de desenvolvimento.

## Verificações

Backend:

```powershell
cd backend
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Frontend:

```powershell
cd frontend
npm run lint
npm run test
npm run build
```

## Estrutura

```text
backend/
  apps/
    contas/   usuários e autenticação do MedPrev
    legado/   modelos das tabelas fictícias importadas
  config/     configurações, URLs e API
frontend/
  src/
    app/      composição da aplicação
    features/ funcionalidades por domínio
    shared/   infraestrutura reutilizável
```
