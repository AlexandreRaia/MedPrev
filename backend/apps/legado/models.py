from django.db import models


class TabelaImportadaModel(models.Model):
    """Base para tabelas fictícias importadas do dump para desenvolvimento."""

    class Meta:
        abstract = True
        managed = False


class Servidor(TabelaImportadaModel):
    cd_servidor = models.IntegerField(primary_key=True)
    nm_servidor = models.TextField()
    nm_social = models.TextField(null=True)
    dt_nascimento = models.DateField(null=True)
    id_sexo = models.TextField(null=True)
    id_estcivil = models.IntegerField(null=True)
    id_racacor = models.IntegerField(null=True)
    nm_pai = models.TextField(null=True)
    nm_mae = models.TextField(null=True)
    nro_rg = models.TextField(null=True)
    dt_rg = models.DateField(null=True)
    ds_exprg = models.TextField(null=True)
    nro_cpf = models.TextField(null=True)
    ds_localnasc = models.TextField(null=True)
    sg_ufnasc = models.TextField(null=True)
    ds_endereco = models.TextField(null=True)
    ds_complemento = models.TextField(null=True)
    ds_bairro = models.TextField(null=True)
    ds_cidade = models.TextField(null=True)
    sg_uf = models.TextField(null=True)
    nro_cep = models.TextField(null=True)
    ds_email = models.TextField(null=True)
    nro_telefone = models.TextField(null=True)
    nro_celular = models.TextField(null=True)
    cd_funcao = models.IntegerField()
    cd_vinculo = models.IntegerField()
    cd_secretaria = models.IntegerField()
    cd_diretoria = models.IntegerField(null=True)
    cd_departamento = models.IntegerField()
    dt_admissao = models.DateField()
    dt_demissao = models.DateField(null=True)
    cd_situacao = models.IntegerField()
    qt_diasestagio = models.IntegerField(null=True)
    qt_diasprorrogestagio = models.IntegerField(null=True)
    dt_vencimentocontrato = models.DateField(null=True)
    st_readaptacao = models.BooleanField(null=True)
    dt_readaptacao = models.DateField(null=True)
    cd_readaptacao = models.IntegerField(null=True)
    id_servidortipo = models.IntegerField(null=True)
    dt_cadastro = models.DateTimeField(null=True)
    codmunicipe = models.IntegerField(null=True)
    codmunicipeold = models.IntegerField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "servidor"


class SituacaoProtocolo(TabelaImportadaModel):
    cd_situacaoprotocolo = models.BigIntegerField(primary_key=True)
    ds_situacaoprotocolo = models.TextField()
    nro_situacaoprotocolo = models.IntegerField(null=True)
    st_admissional = models.TextField(null=True)
    st_demissional = models.TextField(null=True)
    st_administrativo = models.TextField(null=True)
    st_atendimento = models.TextField(null=True)
    st_periodico = models.TextField(null=True)
    ic_alteracao = models.TextField(null=True)
    ic_exclusao = models.TextField(null=True)
    ic_liberacao = models.TextField(null=True)
    ic_validacao = models.TextField(null=True)
    ic_prorrogacao = models.TextField(null=True)
    ic_comentario = models.TextField(null=True)
    ic_documento = models.TextField(null=True)
    ic_cancelamento = models.TextField(null=True)
    ic_guiaexame = models.TextField(null=True)
    ic_avaliacao = models.TextField(null=True)
    ic_licenciamento = models.TextField(null=True)
    ic_finalizacao = models.TextField(null=True)
    ic_validado = models.TextField(null=True)
    st_ativo = models.BooleanField()

    class Meta:
        managed = False
        db_table = "situacaoprotocolo"


class Licenca(TabelaImportadaModel):
    cd_licenca = models.BigIntegerField(primary_key=True)
    dt_licenca = models.DateField(null=True)
    cd_profissional = models.IntegerField(null=True)
    qt_dias = models.IntegerField(null=True)
    dt_inicio = models.DateField(null=True)
    dt_termino = models.DateField(null=True)
    hr_inicio = models.TextField(null=True)
    hr_termino = models.TextField(null=True)
    ic_encaminhamento = models.TextField(null=True)
    ic_retorno = models.TextField(null=True)
    dt_retorno = models.DateField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "licenca"


class Protocolo(TabelaImportadaModel):
    cd_protocolo = models.BigIntegerField(primary_key=True)
    dt_protocolo = models.DateField()
    cd_candidato = models.IntegerField(null=True)
    cd_servidor = models.IntegerField(null=True)
    cd_funcao = models.IntegerField(null=True)
    cd_vinculo = models.IntegerField(null=True)
    cd_secretaria = models.IntegerField(null=True)
    cd_diretoria = models.IntegerField(null=True)
    cd_departamento = models.IntegerField(null=True)
    cd_campanha = models.IntegerField(null=True)
    cd_crmmedico = models.TextField(null=True)
    ds_nomemedico = models.TextField(null=True)
    qt_diasmedico = models.IntegerField(null=True)
    cd_licenca = models.IntegerField(null=True)
    cd_tipoprotocolo = models.IntegerField(null=True)
    cd_situacaoprotocolo = models.IntegerField(null=True)
    id_secretariapub = models.IntegerField(null=True)
    ic_validado = models.TextField(null=True)
    st_status = models.TextField(null=True)
    st_trabalhou = models.BooleanField(null=True)
    id_arquivoassinadoaso = models.IntegerField(null=True)
    num_fonepub = models.TextField(null=True)
    ic_email = models.TextField(null=True)
    st_verificado = models.BooleanField(null=True)
    dt_cadastro = models.DateTimeField(null=True)
    id_usuarioexclusao = models.IntegerField(null=True)
    dt_exclusao = models.DateTimeField(null=True)
    ic_cienciaatestado = models.BooleanField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "protocolo"


class Pericia(TabelaImportadaModel):
    cd_pericia = models.BigIntegerField(primary_key=True)
    dt_pericia = models.DateField(null=True)
    nro_pericia = models.IntegerField(null=True)
    hr_periciaini = models.TextField(null=True)
    hr_periciafim = models.TextField(null=True)
    ds_pericia = models.TextField(null=True)
    cd_profissional = models.IntegerField(null=True)
    cd_licenca = models.IntegerField(null=True)
    cd_protocolo = models.IntegerField(null=True)
    ds_subjetivo = models.TextField(null=True)
    ds_objetivo = models.TextField(null=True)
    ds_conduta = models.TextField(null=True)
    nro_peso = models.IntegerField(null=True)
    nro_abdominal = models.IntegerField(null=True)
    nro_altura = models.IntegerField(null=True)
    nro_temperatura = models.IntegerField(null=True)
    nro_glicemia = models.IntegerField(null=True)
    nro_frequencia = models.IntegerField(null=True)
    nro_sistolica = models.IntegerField(null=True)
    nro_diastolica = models.IntegerField(null=True)
    nro_saturacao = models.IntegerField(null=True)
    ic_declaracao = models.TextField(null=True)
    hr_declaracaoini = models.TextField(null=True)
    hr_declaracaofim = models.TextField(null=True)
    ic_autorizacao = models.TextField(null=True)
    ic_continuacao = models.TextField(null=True)
    ic_riscobiologico = models.TextField(null=True)
    ic_riscoquimico = models.TextField(null=True)
    ic_riscoergonomico = models.TextField(null=True)
    ic_riscofisico = models.TextField(null=True)
    ic_riscoausente = models.TextField(null=True)
    ic_riscomecanico = models.TextField(null=True)
    cd_situacao = models.IntegerField(null=True)
    ds_relatoriomedico = models.TextField(null=True)
    ds_tiposanguineo = models.TextField(null=True)
    ic_atestado = models.TextField(null=True)
    dt_atestado = models.DateField(null=True)
    qt_atestadodias = models.IntegerField(null=True)
    num_processo = models.TextField(null=True)
    ds_historico = models.TextField(null=True)
    ds_conclusao = models.TextField(null=True)
    st_avaliacaosocial = models.BooleanField(null=True)
    st_periciareadaptacao = models.BooleanField(null=True)
    st_periciarestricao = models.BooleanField(null=True)
    id_tipoaltamedica = models.IntegerField(null=True)
    dt_tipoaltamedica = models.DateTimeField(null=True)
    dt_tipoaltamedicaretorno = models.DateTimeField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "pericia"


class ProtocoloCid(TabelaImportadaModel):
    cd_protocolocid = models.BigIntegerField(primary_key=True)
    cd_protocolo = models.IntegerField()
    cd_cid = models.TextField()
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "protocolocid"


class StatusAtendimento(TabelaImportadaModel):
    id_status = models.BigIntegerField(primary_key=True)
    ds_status = models.TextField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "status"


class Atendimento(TabelaImportadaModel):
    id_atendimento = models.BigIntegerField(primary_key=True)
    cd_servidor = models.IntegerField(null=True)
    cd_calendario = models.IntegerField(null=True)
    id_status = models.IntegerField(null=True)
    ds_historicomedico = models.TextField(null=True)
    ds_demandainicial = models.TextField(null=True)
    ds_evolucao = models.TextField(null=True)
    ds_observacao = models.TextField(null=True)
    dt_atendimento = models.DateTimeField(null=True)
    dt_cadastro = models.DateTimeField(null=True)
    id_usuario = models.IntegerField(null=True)
    st_atendido = models.BooleanField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "atendimento"


class TipoEncaminhamento(TabelaImportadaModel):
    id_tipoencaminhamento = models.BigIntegerField(primary_key=True)
    ds_tipoencaminhamento = models.TextField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "tipoencaminhamento"


class Encaminhamento(TabelaImportadaModel):
    id_encaminhamento = models.BigIntegerField(primary_key=True)
    id_atendimento = models.IntegerField(null=True)
    id_tipoencaminhamento = models.IntegerField(null=True)
    dt_encaminhamento = models.DateTimeField(null=True)
    ds_observacao = models.TextField(null=True)
    dt_cadastro = models.DateTimeField(null=True)
    id_usuario = models.IntegerField(null=True)
    st_ativo = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = "encaminhamento"
