# Dicionário do dump fictício de desenvolvimento

Inventário obtido do dump fictício `sismed.dump`. O arquivo foi gerado pelo
PostgreSQL 16.14 em 23/07/2026, usa codificação UTF-8 e contém o schema `dbo`.

O dump é um artefato de desenvolvimento e não deve ser versionado. Dumps reais
também nunca devem ser adicionados ao repositório.

## Resumo

- 92 tabelas;
- 92 conjuntos de dados;
- 88 chaves primárias ou restrições não relacionais;
- 26 chaves estrangeiras declaradas;
- 82 sequências;
- todos os dados analisados são fictícios.

Muitas relações funcionais aparecem apenas como colunas `cd_*` ou `id_*`, sem
uma chave estrangeira declarada no banco. Por isso, os primeiros modelos Django
mantêm essas referências como IDs escalares. A promoção para `ForeignKey` só
deve ocorrer após validação da cardinalidade e do comportamento com dados
do produto.

## Primeira fase mapeada

| Tabela | Registros | Chave primária | Papel |
|---|---:|---|---|
| `servidor` | 20 | `cd_servidor` | Identificação e situação funcional do servidor |
| `protocolo` | 30 | `cd_protocolo` | Processo de saúde que agrupa os eventos |
| `situacaoprotocolo` | 3 | `cd_situacaoprotocolo` | Domínio de situação do protocolo |
| `licenca` | 10 | `cd_licenca` | Período oficial de afastamento |
| `pericia` | 10 | `cd_pericia` | Avaliação, relatório e conclusão médica |

### Validações da amostra

- todos os 30 protocolos possuem `cd_servidor`;
- nenhum `protocolo.cd_servidor` aponta para servidor inexistente;
- nenhum `protocolo.cd_situacaoprotocolo` aponta para situação inexistente;
- os 20 servidores possuem entre um e dois protocolos;
- as 10 perícias apontam para protocolos, licenças e profissionais existentes;
- somente os protocolos de 1 a 10 possuem perícia na amostra;
- todos os 30 valores de `protocolo.cd_licenca` são nulos;
- as situações são `1 - Aberto`, `2 - Em analise` e `3 - Finalizado`;
- todos os servidores e protocolos fictícios estão ativos;
- todas as licenças têm `qt_dias = 3`, enquanto `dt_termino - dt_inicio = 3`.

O último item não resolve se a contagem deve ser inclusiva ou exclusiva. O
cálculo deve continuar pendente até validação da regra de negócio.

## Campos prioritários

### `servidor`

- identificação: `cd_servidor`, `nm_servidor`, `nm_social`, `nro_cpf`,
  `nro_rg`;
- contato: `ds_email`, `nro_telefone`, `nro_celular`, endereço;
- lotação: `cd_funcao`, `cd_vinculo`, `cd_secretaria`, `cd_diretoria`,
  `cd_departamento`;
- situação: `cd_situacao`, `dt_admissao`, `dt_demissao`, `st_ativo`;
- saúde funcional: campos de readaptação e tipo de servidor.

### `protocolo`

- identificação e data: `cd_protocolo`, `dt_protocolo`;
- vínculos: `cd_servidor`, `cd_licenca`, `cd_tipoprotocolo`,
  `cd_situacaoprotocolo`;
- documento médico: `cd_crmmedico`, `ds_nomemedico`, `qt_diasmedico`;
- estado: `st_status`, `st_verificado`, `st_ativo`;
- exclusão lógica: `id_usuarioexclusao`, `dt_exclusao`;
- cadastro: `dt_cadastro`.

### `situacaoprotocolo`

- identificação: `cd_situacaoprotocolo`;
- descrição e ordem: `ds_situacaoprotocolo`, `nro_situacaoprotocolo`;
- permissões funcionais: campos `ic_*` e `st_*`;
- estado: `st_ativo`.

### `licenca`

- identificação: `cd_licenca`;
- datas oficiais: `dt_inicio`, `dt_termino`;
- quantidade informada: `qt_dias`;
- profissional: `cd_profissional`;
- retorno: `ic_retorno`, `dt_retorno`;
- estado: `st_ativo`.

### `pericia`

- identificação: `cd_pericia`, `nro_pericia`, `dt_pericia`;
- vínculos: `cd_profissional`, `cd_licenca`, `cd_protocolo`;
- conteúdo clínico: `ds_subjetivo`, `ds_objetivo`, `ds_conduta`,
  `ds_relatoriomedico`, `ds_historico`, `ds_conclusao`;
- atestado: `ic_atestado`, `dt_atestado`, `qt_atestadodias`;
- alta: `id_tipoaltamedica`, `dt_tipoaltamedica`,
  `dt_tipoaltamedicaretorno`;
- estado: `cd_situacao`, `st_ativo`.

## Demais tabelas prioritárias

| Tabela | Registros | Uso esperado |
|---|---:|---|
| `protocololog` | 30 | Movimentações e mudanças de situação |
| `protocoloobs` | 10 | Observações do protocolo |
| `protocolocid` | 10 | CIDs do protocolo |
| `profissional` | 5 | Profissional responsável |
| `calendario` | 30 | Agendamentos e comparecimento |
| `atendimento` | 30 | Atendimento e evolução clínica |
| `ocorrencia` | 5 | Eventos, faltas e cancelamentos |
| `documento` | 10 | Documentos de atendimento |
| `protocolodocto` | 5 | Documentos anexados ao protocolo |
| `encaminhamento` | 10 | Encaminhamentos de atendimento |

Essas tabelas serão mapeadas gradualmente conforme os fluxos do produto forem
desenvolvidos sobre o SQLite local.

## Inventário completo

```text
agenda (10)
atendimento (30)
calendario (30)
campanha (1)
campanhaexame (5)
candidato (10)
cidnaoperdebeneficio (1)
combinado (1)
combinadoexame (5)
deficienciaauditiva (1)
deficienciafisica (1)
deficienciaintelectual (1)
deficienciamental (1)
deficienciamultipla (1)
deficienciaorigem (1)
deficienciavisual (1)
departamento (4)
diretoria (2)
documento (10)
documentoatestado (5)
encaminhamento (10)
estcivil (3)
exame (5)
faixa (2)
ferias (5)
filatotem (5)
funcao (5)
funcaodescricao (1)
funcaoxrestricao (1)
grupoderisco (2)
grupoderiscoagnoc (1)
grupoderiscoepi (1)
grupoderiscoepicompl (1)
grupoderiscoepiepc (1)
grupoderiscoxfuncao (2)
guia (10)
guiaexame (10)
historicoavaliacaosocial (5)
integracaoprotocolo (10)
licenca (10)
local (2)
logconectacecam (1)
notificarservidoratestado (5)
ocorrencia (5)
orientacao (1)
pacientecontato (10)
pericia (10)
periciapcd (1)
periciapcdxdeficienciaauditiva (1)
periciapcdxdeficienciafisica (1)
periciapcdxdeficienciaintelectual (1)
periciapcdxdeficienciamental (1)
periciapcdxdeficienciamultipla (1)
periciapcdxdeficienciaorigem (1)
periciapcdxdeficienciavisual (1)
periciareadaptacao (1)
periciarestricao (1)
periciaxfuncaoxrestricao (1)
profissional (5)
protocolo (30)
protocoloassinatura (5)
protocolocid (10)
protocolodeclaracao (5)
protocolodocto (5)
protocololog (30)
protocoloobs (10)
racacor (5)
secretaria (3)
secretariaxfuncao (5)
sequencia (10)
servidor (20)
servidortipo (2)
setor (3)
situacaoexame (3)
situacaoguia (3)
situacaoprotocolo (3)
situacaoservidor (3)
status (3)
temp (1)
tipoaltamedica (2)
tipocondicao (3)
tipodocto (2)
tipodoctopsicologico (2)
tipodocumento (3)
tipoencaminhamento (3)
tipoexame (3)
tipoguia (3)
tipoocorrencia (2)
tipoprotocolo (3)
tiporelatorio (2)
tiporesultado (2)
vinculo (3)
```

## Restrições conhecidas

O dump declara FKs para alguns módulos, como:

- `atendimento.cd_calendario -> calendario.cd_calendario`;
- `protocololog.cd_protocolo -> protocolo.cd_protocolo`;
- `protocololog.cd_situacaoprotocolo ->
  situacaoprotocolo.cd_situacaoprotocolo`;
- `documento.id_atendimento -> atendimento.id_atendimento`;
- `encaminhamento.id_atendimento -> atendimento.id_atendimento`.

Não há FKs declaradas no dump para as principais relações entre `protocolo`,
`servidor`, `licenca` e `pericia`. Elas devem ser tratadas como relações
funcionais a validar, não como garantias físicas do banco.
