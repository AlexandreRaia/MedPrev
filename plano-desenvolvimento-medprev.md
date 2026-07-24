# Plano de Desenvolvimento do MedPrev

**Status:** plano-base para validação  
**Objetivo:** orientar a construção incremental do MedPrev com Django, Django Ninja, React, TypeScript e PostgreSQL, preservando o SisMed como fonte oficial somente leitura.

## 1. Resultado esperado

Entregar uma aplicação web segura para consultar dados operacionais do SisMed e executar os fluxos próprios do MedPrev, incluindo controle de acesso, pareceres médicos, anexos e auditoria.

O desenvolvimento será feito em pequenas fatias verticais. Cada fatia deve incluir regra de negócio, autorização no backend, API, interface, testes e tratamento de erros. A prioridade é código simples, explícito e compreensível por desenvolvedores juniores.

## 2. Decisões já confirmadas

| Tema | Decisão |
| --- | --- |
| Arquitetura | Monólito modular, sem microserviços |
| Backend | Python, Django e Django Ninja |
| Frontend | React com TypeScript |
| Banco próprio | PostgreSQL |
| Sistema oficial | O SisMed permanece como fonte oficial dos dados operacionais |
| Integração | O MedPrev consulta o SisMed, mas nunca grava, altera, migra ou exclui dados nele |
| Dados do MedPrev | Usuários, grupos, permissões, pareceres, anexos, auditoria e outros dados explicitamente aprovados |
| Relações entre bancos | Sem chaves estrangeiras entre PostgreSQL e SisMed; usar identificadores externos explícitos |
| Autorização | Usuários, grupos e permissões nativos do Django; verificação obrigatória no backend |
| Qualidade | Solução simples, segura, legível, testada e sem abstrações prematuras |

## 3. Decisões funcionais pendentes

Estas definições precisam ser aprovadas antes das funcionalidades correspondentes. Elas não devem ser inventadas durante a implementação.

1. Quais perfis de usuário existirão e quais ações cada perfil poderá executar.
2. Se o acesso será global ou limitado por unidade, lotação, vínculo, responsabilidade ou outro critério.
3. Quais entidades e campos do SisMed poderão ser consultados e exibidos.
4. Quais campos compõem um parecer médico.
5. Quais estados um parecer poderá ter e quais transições serão permitidas.
6. Quem poderá criar, editar, concluir, assinar, reabrir, cancelar ou visualizar um parecer.
7. Se o parecer precisará guardar uma fotografia de dados do SisMed para preservação histórica.
8. Quantidade, formatos, tamanhos, armazenamento e prazo de retenção dos anexos.
9. Quais eventos de visualização, alteração e administração precisam entrar na trilha de auditoria e por quanto tempo devem ser retidos.
10. Forma de autenticação: sessão Django, diretório institucional ou outro provedor de identidade.
11. Ambientes, infraestrutura de implantação, domínio, HTTPS, armazenamento privado de arquivos, backups e monitoramento.
12. Requisitos institucionais e jurídicos aplicáveis a dados de saúde, impressão, exportação e compartilhamento.

Essas decisões devem ser registradas em um documento curto de regras do produto e em uma matriz de permissões.

## 4. Arquitetura proposta

```text
medprev/
  backend/
    config/
    apps/
      contas/
      legado/
      pareceres/
      anexos/
      auditoria/
  frontend/
    src/
      app/
      features/
      shared/
```

- `contas`: usuário próprio baseado em `AbstractUser`, grupos, permissões e administração.
- `legado`: modelos não gerenciados e consultas explícitas ao SisMed.
- `pareceres`: dados, regras e ciclo de vida dos pareceres.
- `anexos`: metadados, armazenamento privado e autorização de acesso.
- `auditoria`: eventos relevantes de segurança e negócio.

O banco `default` será o PostgreSQL do MedPrev. O alias `sismed` será usado exclusivamente para leitura do legado.

## 5. Estratégia de entrega

Cada marco deve gerar uma versão demonstrável. Dentro de cada funcionalidade, a ordem será:

1. critérios de aceitação;
2. modelo de dados e permissões;
3. regra e proteção no backend;
4. contrato da API;
5. interface React;
6. testes e revisão de segurança;
7. demonstração e aceite.

Não será criado todo o backend antes do frontend. Cada fluxo será concluído ponta a ponta antes de iniciar o próximo fluxo de mesmo nível de prioridade.

## 6. Marcos de desenvolvimento

### Marco 0 — Descoberta e fechamento do MVP

**Objetivo:** remover ambiguidades que afetam autorização, dados e segurança.

**Entregas:**

- mapa dos usuários e dos fluxos clínicos;
- matriz de perfis, permissões e possíveis restrições por objeto;
- lista das consultas necessárias ao SisMed;
- campos e ciclo de vida do parecer;
- política inicial de anexos;
- eventos e retenção da auditoria;
- escopo fechado do MVP;
- critérios de aceitação dos primeiros fluxos.

**Critério de conclusão:** o MVP pode ser descrito como comportamentos observáveis, e as decisões pendentes que bloqueiam o primeiro fluxo estão aprovadas.

### Marco 1 — Fundação técnica

**Objetivo:** preparar uma base mínima, reproduzível e segura.

**Entregas:**

- estrutura do backend e do frontend;
- configurações separadas por ambiente;
- PostgreSQL do MedPrev;
- modelo de usuário próprio desde a primeira migration;
- API versionada em `/api/v1`;
- aplicação React com rotas e layout básico;
- variáveis de ambiente e segredos fora do código;
- comandos documentados para executar projeto, migrations e testes;
- formatter, linter e verificação de tipos usando o menor conjunto adequado ao projeto;
- testes de inicialização e endpoint de saúde;
- dados de desenvolvimento exclusivamente sintéticos.

**Critério de conclusão:** um desenvolvedor consegue iniciar backend, frontend e PostgreSQL seguindo a documentação; verificações automáticas básicas passam.

### Marco 2 — Autenticação, autorização e administração

**Objetivo:** estabelecer identidade e controle de acesso antes de expor dados sensíveis.

**Entregas:**

- autenticação definida no Marco 0;
- sessão, cookies e CSRF configurados com segurança quando aplicáveis;
- grupos e permissões por ação de negócio;
- usuário, grupos e permissões administráveis pelo Django Admin;
- endpoint de sessão do usuário com permissões necessárias à interface;
- proteção de rotas no backend;
- estados de acesso negado no frontend;
- auditoria mínima de autenticação e alterações de acesso.

**Critério de conclusão:** testes demonstram o comportamento de usuário não autenticado, autenticado sem permissão e autenticado com permissão, inclusive por chamada direta à API.

### Marco 3 — Integração somente leitura com o SisMed

**Objetivo:** disponibilizar as consultas externas necessárias ao primeiro fluxo sem risco de escrita.

**Entregas:**

- conexão separada com credencial de banco exclusivamente leitora;
- modelos legados com `managed = False`;
- router de banco que impeça migrations no SisMed;
- bloqueios explícitos contra `save`, `create`, `update` e `delete` nos caminhos da aplicação;
- módulos de consulta por domínio, sem expor `QuerySet` legado ao restante do sistema;
- paginação, limites, seleção apenas dos campos necessários e erros seguros;
- testes que comprovem uso do alias correto e recusa de escrita;
- tratamento de indisponibilidade e inconsistência do legado.

**Critério de conclusão:** o fluxo aprovado consulta dados reais do ambiente autorizado, e as proteções técnicas e de credencial impedem gravação no SisMed.

### Marco 4 — Primeira fatia vertical de consulta

**Objetivo:** validar arquitetura, permissões, contrato da API e experiência do usuário em um fluxo completo.

**Escopo proposto:** selecionar uma consulta prioritária aprovada no Marco 0 — por exemplo, localizar um servidor ou protocolo e visualizar apenas os dados necessários para o trabalho médico.

**Entregas:**

- busca paginada com filtros permitidos;
- tela de resultados com estados de carregamento, vazio, erro e acesso negado;
- tela de detalhe com exposição mínima de dados;
- autorização no backend;
- auditoria das visualizações definidas como sensíveis;
- testes de API, componente e um teste ponta a ponta do fluxo.

**Critério de conclusão:** um usuário autorizado conclui o primeiro fluxo útil do MedPrev; usuários sem permissão não obtêm nem confirmam a existência de dados sensíveis.

### Marco 5 — Pareceres médicos

**Objetivo:** implementar o principal dado próprio do MedPrev após aprovação de campos, estados e permissões.

**Entregas:**

- modelo relacional com constraints para invariantes confirmadas;
- identificador externo explícito, como `servidor_sismed_id` ou o identificador aprovado;
- migrations pequenas e revisadas, somente no PostgreSQL do MedPrev;
- APIs com schemas explícitos de entrada, saída e erro;
- validação das transições de estado no backend;
- telas de listagem, detalhe e ações aprovadas;
- prevenção de envio duplicado e tratamento de conflito de edição quando necessário;
- auditoria gravada na mesma transação das alterações locais relevantes;
- testes de autorização, validação, transação, conflito e transições.

**Critério de conclusão:** os fluxos de parecer aprovados funcionam ponta a ponta e nenhuma regra importante depende apenas do React.

### Marco 6 — Anexos

**Objetivo:** permitir anexos privados somente depois de aprovar regras de armazenamento e acesso.

**Entregas:**

- armazenamento fora da área pública;
- metadados mínimos: nome seguro, tipo declarado e detectado quando disponível, tamanho, chave, autor e datas;
- validação de nome, tipo e tamanho;
- upload e download sempre autorizados no backend;
- download sem exposição do caminho físico;
- auditoria de upload e download;
- testes com arquivo inválido, excesso de tamanho, acesso negado, ausência e sucesso.

**Critério de conclusão:** nenhum anexo é acessível por URL pública ou por usuário sem permissão, e os limites aprovados são aplicados no servidor.

### Marco 7 — Auditoria e operação

**Objetivo:** completar a rastreabilidade e preparar suporte sem registrar conteúdo médico desnecessário.

**Entregas:**

- catálogo dos eventos auditáveis;
- evento com ator, ação, alvo, instante e contexto mínimo;
- trilha append-only no fluxo normal;
- consulta administrativa restrita quando aprovada;
- separação entre logs técnicos e auditoria;
- identificador de requisição, duração e resultado nos logs técnicos;
- ausência de pareceres, diagnósticos, tokens, senhas e conteúdo de anexos nos logs;
- política de retenção e acesso aplicada.

**Critério de conclusão:** ações sensíveis autorizadas geram o evento correto; falhas não registram sucesso; apenas perfis aprovados acessam a trilha.

### Marco 8 — Homologação, segurança e implantação

**Objetivo:** validar o MVP em condições próximas da produção.

**Entregas:**

- testes de regressão dos fluxos críticos;
- revisão da matriz de autorização;
- teste de migrations em banco vazio e em estado representativo anterior;
- verificação de HTTPS, cookies, CSRF, CORS e cabeçalhos;
- validação de backup e recuperação do PostgreSQL e dos anexos;
- monitoramento de disponibilidade e erros sem dados sensíveis;
- documentação operacional e procedimento de implantação;
- homologação com usuários responsáveis;
- plano de reversão da versão.

**Critério de conclusão:** critérios do MVP foram aceitos, verificações automatizadas passam e existe procedimento seguro de implantação e recuperação.

## 7. Backlog priorizado

| Prioridade | Épico | Dependência principal |
| --- | --- | --- |
| P0 | Fechar regras do MVP e matriz de acesso | Responsáveis funcionais |
| P0 | Fundação técnica | Ambiente de desenvolvimento |
| P0 | Autenticação e autorização | Matriz de acesso |
| P0 | Proteção somente leitura do SisMed | Acesso e esquema do SisMed |
| P0 | Primeira consulta vertical | Consulta prioritária aprovada |
| P0 | Fluxo mínimo de parecer | Campos, estados e permissões aprovados |
| P1 | Anexos | Política de arquivos e infraestrutura |
| P1 | Auditoria completa | Catálogo e retenção aprovados |
| P1 | Homologação e implantação | Ambientes disponíveis |
| P2 | Melhorias de desempenho | Métricas e problema demonstrado |
| P2 | Funcionalidades adicionais | MVP homologado |

Itens P2 não devem atrasar o MVP.

## 8. Estratégia mínima de testes

| Camada | Cobertura principal |
| --- | --- |
| API e integração | autenticação, autorização, validação, persistência, transações, erros e SisMed somente leitura |
| Unidade | regras puras, transições e políticas de domínio |
| Componentes React | carregamento, vazio, erro, acesso negado, formulário e sucesso |
| Ponta a ponta | autenticar, executar a consulta prioritária, realizar o fluxo aprovado de parecer e acessar anexo autorizado |
| Migrations | banco vazio, versão anterior representativa e confirmação de que o SisMed não é afetado |

Todo fluxo sensível deve testar:

- usuário não autenticado;
- usuário sem permissão;
- usuário com permissão;
- restrição por objeto ou unidade, se aprovada;
- tentativa direta pela API;
- falha externa ou dado ausente;
- ausência de dados sensíveis em erro e log.

## 9. Definição de pronto

Uma funcionalidade só será considerada pronta quando:

- seus critérios de aceitação forem observáveis e atendidos;
- a autorização estiver implementada no backend;
- o SisMed continuar estritamente somente leitura;
- migrations aplicáveis tiverem sido revisadas;
- carregamento, vazio, erro, acesso negado e sucesso estiverem tratados;
- testes proporcionais ao risco estiverem passando;
- formatter, linter e tipos configurados estiverem passando;
- logs e erros não expuserem dados sensíveis;
- contrato da API e decisão funcional relevante estiverem atualizados;
- não houver TODO vago, código morto ou mudança não relacionada.

## 10. Riscos e respostas

| Risco | Resposta planejada |
| --- | --- |
| Regras de parecer incompletas | fechar campos, estados e permissões antes do Marco 5 |
| Escrita acidental no SisMed | credencial leitora, alias explícito, modelos não gerenciados, router, bloqueios e testes |
| Exposição de dados de saúde | menor privilégio, campos mínimos, autorização no backend e revisão de logs |
| Diferenças ou inconsistências no legado | tratar ausência explicitamente sem corrigir o SisMed pelo MedPrev |
| Escopo crescente | manter MVP fechado e mover melhorias sem dependência para P2 |
| Abstrações prematuras | aceitar código direto e pequena repetição quando forem mais claros |
| Dependência de infraestrutura para anexos | decidir armazenamento, limites, backup e retenção antes do Marco 6 |
| Estimativas irreais | estimar calendário somente após conhecer equipe, disponibilidade, ambientes e escopo aprovado |

## 11. Próxima ação recomendada

Realizar uma reunião curta de definição do Marco 0 e responder às decisões pendentes dos itens 1 a 7. Em seguida, transformar a primeira consulta e o fluxo mínimo de parecer em critérios de aceitação. Só então estimar duração e distribuir responsáveis.

