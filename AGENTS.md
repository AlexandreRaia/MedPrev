# Regras de desenvolvimento do MedPrev

## Banco fictício de desenvolvimento

- Não há conexão com o SisMed institucional durante o desenvolvimento.
- O arquivo `sismed.dump` contém somente dados fictícios e serve como fonte
  para o `backend/db.sqlite3`.
- As tabelas importadas ficam no banco `default` e permitem leitura e escrita.
- Não criar um segundo arquivo SQLite nem um alias de banco chamado `sismed`.
- Os modelos das tabelas importadas permanecem `managed = False`; a estrutura
  é recriada pelo comando de importação, não por migrations.
- Relações não garantidas pelo schema permanecem como IDs escalares até serem
  validadas com as regras do produto.

## Organização do backend

- Consultas complexas e composição de leitura ficam em `selectors.py`.
- Regras de negócio e gravações ficam em `services.py`.
- Todas as leituras e escritas de desenvolvimento usam o banco `default`.
- A linha do tempo deve ser montada no backend.
- Todo endpoint deve verificar autenticação e permissão.
- Parecer finalizado não pode ser sobrescrito; alterações geram retificação.

## Compatibilidade e validação

- O SQLite é temporário e usado somente para desenvolvimento local.
- O destino futuro é PostgreSQL.
- Modelos e migrations próprios do MedPrev devem permanecer compatíveis com
  PostgreSQL.
- Não inferir regras clínicas ou cardinalidades ausentes no schema.
- Criar testes para banco correto, permissões e serialização da timeline.
- Executar `ruff format --check`, `ruff check`, `manage.py check` e
  `manage.py test` antes de concluir alterações no backend.
