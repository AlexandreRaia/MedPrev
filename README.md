# MedPrev

Base full-stack do MedPrev, organizada como um monólito modular:

- Django e Django Ninja no backend;
- React com TypeScript no frontend;
- PostgreSQL para os dados próprios do MedPrev;
- integração futura com o SisMed estritamente somente leitura.

Esta primeira estrutura entrega uma API versionada, um endpoint de saúde, uma
tela React que consulta esse endpoint, um usuário Django próprio e proteções de
código contra escrita nos modelos legados. Regras ainda não aprovadas de
pareceres, anexos, auditoria e permissões não foram inventadas.

## Pré-requisitos

- Python 3.12;
- Node.js 20.19 ou superior;
- Docker com Docker Compose somente quando o PostgreSQL for habilitado.

## Iniciar o ambiente

Na raiz do projeto, crie a configuração local. Enquanto o PostgreSQL não
estiver disponível, o ambiente de desenvolvimento usa SQLite:

```bash
cp .env.example .env
```

Prepare e inicie o backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Em outro terminal, prepare e inicie o frontend:

```bash
cd frontend
npm ci
npm run dev
```

A aplicação fica em <http://localhost:5173>, a API em
<http://localhost:8000/api/v1/> e, durante o desenvolvimento, a documentação
OpenAPI em <http://localhost:8000/api/v1/docs>.

### Habilitar PostgreSQL

O SQLite é uma solução temporária para o desenvolvimento local. Para usar o
PostgreSQL, altere `DATABASE_ENGINE=postgresql` no `.env` e inicie o serviço:

```bash
docker compose up -d postgres
```

As migrations e os modelos devem permanecer compatíveis com PostgreSQL. Não
adicione SQL específico do SQLite nem trate o arquivo `db.sqlite3` como dado
permanente.

## Verificações

Backend:

```bash
cd backend
ruff format --check .
ruff check .
python manage.py check
python manage.py test
```

Frontend:

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## Fronteira de dados

O PostgreSQL configurado como `default` pertence ao MedPrev. O alias `sismed`
é reservado ao banco legado e não é necessário para executar esta estrutura
inicial.

Antes de configurar o SisMed:

1. confirme o mecanismo e o esquema do banco legado;
2. obtenha uma credencial com permissão exclusiva de leitura;
3. crie modelos `managed = False` que herdem de
   `SisMedSomenteLeituraModel`;
4. mantenha todas as consultas no alias `sismed`;
5. adicione testes que comprovem a leitura no alias correto e a recusa de
   escrita.

Nunca crie chaves estrangeiras entre os dois bancos. O MedPrev deve guardar
somente o identificador externo necessário, com um nome explícito como
`servidor_sismed_id`.

## Estrutura

```text
backend/
  apps/
    contas/   usuário próprio do MedPrev
    legado/   fronteira somente leitura do SisMed
  config/     configurações, URLs e API
frontend/
  src/
    app/      composição da aplicação
    features/ funcionalidades por domínio
    shared/   infraestrutura pequena e reutilizável
```

Novos apps e módulos devem surgir junto com uma fatia funcional aprovada. A
próxima etapa depende da definição do MVP, da matriz de permissões e da primeira
consulta prioritária ao SisMed.
