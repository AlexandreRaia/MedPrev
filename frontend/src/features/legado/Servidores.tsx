import { FormEvent, useEffect, useState } from "react";

import {
  criarSolicitacao,
  Especialidade,
  listarSolicitacoesDoServidor,
  SolicitacaoApoio,
} from "../apoio/api";
import {
  concluirParecer,
  criarParecer,
  editarParecer,
  listarPareceres,
  Parecer,
} from "../pareceres/api";
import { ApiError } from "../../shared/api/client";
import {
  buscarServidores,
  consultarServidor,
  PericiaResumo,
  ServidorDetalhe,
  ServidorResumo,
} from "./api";

const CONCLUSOES_DO_PARECER = [
  { valor: "apto", rotulo: "Apto para o trabalho" },
  { valor: "afastamento", rotulo: "Necessita afastamento" },
  { valor: "encaminhamento", rotulo: "Necessita encaminhamento" },
  { valor: "acompanhamento", rotulo: "Manter em acompanhamento" },
];

const TAMANHO_MINIMO_DA_BUSCA = 3;

type GrupoCid = { codigo: string; ocorrencias: number; dias: number };

function agruparPorCid(pericias: PericiaResumo[]): GrupoCid[] {
  const mapa = new Map<string, GrupoCid>();
  for (const pericia of pericias) {
    for (const codigo of pericia.cids) {
      const atual = mapa.get(codigo) ?? { codigo, ocorrencias: 0, dias: 0 };
      atual.ocorrencias += 1;
      atual.dias += pericia.atestado ? (pericia.dias_atestado ?? 0) : 0;
      mapa.set(codigo, atual);
    }
  }
  return [...mapa.values()].sort((a, b) => b.dias - a.dias);
}

export function Servidores({
  permissoes,
  usuarioId,
}: {
  permissoes: string[];
  usuarioId: number;
}) {
  const [termo, setTermo] = useState("");
  const [buscaEnviada, setBuscaEnviada] = useState("");
  const [servidores, setServidores] = useState<ServidorResumo[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [selecionado, setSelecionado] = useState<number | null>(null);

  useEffect(() => {
    if (!buscaEnviada) return;
    const controlador = new AbortController();
    buscarServidores(buscaEnviada, controlador.signal)
      .then((resultado) => {
        setServidores(resultado);
        setErro(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setErro(mensagemDoErro(error));
      })
      .finally(() => setCarregando(false));
    return () => controlador.abort();
  }, [buscaEnviada]);

  function submeterBusca(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const termoNormalizado = termo.trim();
    if (termoNormalizado.length < TAMANHO_MINIMO_DA_BUSCA) return;
    setCarregando(true);
    setErro(null);
    setBuscaEnviada(termoNormalizado);
  }

  return (
    <>
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Consulta</p>
          <h1>Consulta de servidores</h1>
          <p>Localize um servidor por nome, nome social, CPF ou prontuário.</p>
        </div>
      </header>
      <section className="painel">
        <form className="barra-filtros" onSubmit={submeterBusca}>
          <label className="campo-busca">
            <span>Buscar por nome, CPF ou prontuário</span>
            <input
              value={termo}
              onChange={(event) => setTermo(event.target.value)}
              placeholder="Ex.: Maria da Silva, CPF ou P1001"
            />
          </label>
          <button
            className="botao botao--primario"
            type="submit"
            disabled={termo.trim().length < TAMANHO_MINIMO_DA_BUSCA}
          >
            Buscar
          </button>
        </form>

        {erro ? (
          <p className="mensagem-erro" role="alert">
            {erro}
          </p>
        ) : null}

        {carregando ? (
          <div className="estado-painel" aria-live="polite">
            <span className="carregando-indicador" aria-hidden="true" />
            <p>Buscando servidores…</p>
          </div>
        ) : null}

        {!carregando && buscaEnviada && !erro && servidores.length === 0 ? (
          <div className="estado-painel">
            <p>Nenhum servidor encontrado para "{buscaEnviada}".</p>
          </div>
        ) : null}

        {!carregando && !buscaEnviada ? (
          <div className="estado-painel">
            <p>Digite um termo de busca para localizar um servidor.</p>
          </div>
        ) : null}

        {!carregando && buscaEnviada && !erro && servidores.length > 0 ? (
          <div className="resultado-cabecalho">
            <span className="contador-registros">
              <strong>{servidores.length}</strong> registro(s) encontrado(s)
            </span>
            <span className="texto-secundario">Última sincronização: agora</span>
          </div>
        ) : null}

        {!carregando && servidores.length > 0 ? (
          <div className="tabela-responsiva">
            <table>
              <thead>
                <tr>
                  <th>Servidor</th>
                  <th>CPF</th>
                  <th>Prontuário</th>
                  <th>Tramitação</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {servidores.map((servidor) => (
                  <tr key={servidor.id}>
                    <td>
                      <div className="identidade-usuario">
                        <span aria-hidden="true">
                          {iniciais(servidor.nome_social ?? servidor.nome)}
                        </span>
                        <div>
                          <strong>{servidor.nome_social ?? servidor.nome}</strong>
                          {servidor.email ? <small>{servidor.email}</small> : null}
                        </div>
                      </div>
                    </td>
                    <td>{servidor.cpf ?? "—"}</td>
                    <td>
                      <span className="codigo-prontuario">P{servidor.id}</span>
                    </td>
                    <td>
                      {servidor.tramitacao ? (
                        <span className="etiqueta-situacao">{servidor.tramitacao}</span>
                      ) : (
                        <span className="texto-secundario">Sem protocolo</span>
                      )}
                    </td>
                    <td className="celula-acao">
                      <button
                        className="botao-historico"
                        type="button"
                        onClick={() => setSelecionado(servidor.id)}
                      >
                        <span aria-hidden="true">☰</span> Ver histórico
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
      {selecionado !== null ? (
        <DetalheServidorModal
          key={selecionado}
          servidorId={selecionado}
          permissoes={permissoes}
          usuarioId={usuarioId}
          aoFechar={() => setSelecionado(null)}
        />
      ) : null}
    </>
  );
}

export function DetalheServidorModal({
  servidorId,
  permissoes,
  usuarioId,
  aoFechar,
}: {
  servidorId: number;
  permissoes: string[];
  usuarioId: number;
  aoFechar: () => void;
}) {
  const [detalhe, setDetalhe] = useState<ServidorDetalhe | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [aba, setAba] = useState<"linha" | "grafico">("linha");

  useEffect(() => {
    const controlador = new AbortController();
    consultarServidor(servidorId, controlador.signal)
      .then(setDetalhe)
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setErro(mensagemDoErro(error));
      })
      .finally(() => setCarregando(false));
    return () => controlador.abort();
  }, [servidorId]);

  const nomeExibido = detalhe?.nome_social ?? detalhe?.nome ?? "Servidor";
  const gruposCid = agruparPorCid(detalhe?.pericias ?? []);
  const maiorDiasPorCid = Math.max(1, ...gruposCid.map((grupo) => grupo.dias));

  const protocolosUltimos60Dias = (detalhe?.protocolos ?? []).filter((protocolo) =>
    dentroDosUltimos60Dias(protocolo.data),
  );
  const periciasUltimos60Dias = (detalhe?.pericias ?? []).filter((pericia) =>
    dentroDosUltimos60Dias(pericia.data),
  );
  const diasDeAtestado60Dias = periciasUltimos60Dias.reduce(
    (total, pericia) => total + (pericia.atestado ? (pericia.dias_atestado ?? 0) : 0),
    0,
  );

  return (
    <div className="modal-fundo" role="presentation">
      <section className="modal modal--prontuario" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <div className="prontuario-identidade">
            <span className="avatar avatar--prontuario" aria-hidden="true">
              {detalhe ? iniciais(nomeExibido) : ""}
            </span>
            <h2>{nomeExibido}</h2>
            {detalhe ? <span className="prontuario-codigo">P{detalhe.id}</span> : null}
            {detalhe ? (
              <span
                className={`indicador-status ${detalhe.ativo ? "indicador-status--ativo" : "indicador-status--inativo"}`}
              >
                <i aria-hidden="true" />
                {detalhe.ativo ? "Ativo" : "Inativo"}
              </span>
            ) : null}
          </div>
          <button className="fechar-modal" onClick={aoFechar} aria-label="Fechar">
            ×
          </button>
        </div>

        {carregando ? (
          <div className="estado-painel" aria-live="polite">
            <span className="carregando-indicador" aria-hidden="true" />
            <p>Carregando dados do servidor…</p>
          </div>
        ) : null}

        {erro ? (
          <p className="mensagem-erro" role="alert">
            {erro}
          </p>
        ) : null}

        {!carregando && !erro && detalhe ? (
          <div className="prontuario-corpo">
            <div className="prontuario-principal">
              {detalhe.tramitacao ? (
                <div className="banner-tramitacao">
                  <span aria-hidden="true">☰</span>
                  <div>
                    <p>Tramitação atual</p>
                    <strong>{detalhe.tramitacao}</strong>
                  </div>
                </div>
              ) : null}
              <h3>Dados do servidor</h3>
              <dl className="lista-dados">
                <div>
                  <dt>
                    <span aria-hidden="true">▤</span> CPF
                  </dt>
                  <dd>{detalhe.cpf ?? "—"}</dd>
                </div>
                <div>
                  <dt>
                    <span aria-hidden="true">◷</span> Nascimento
                  </dt>
                  <dd>{formatarData(detalhe.nascimento)}</dd>
                </div>
                <div>
                  <dt>
                    <span aria-hidden="true">✉</span> E-mail
                  </dt>
                  <dd>{detalhe.email ?? "—"}</dd>
                </div>
                <div>
                  <dt>
                    <span aria-hidden="true">☏</span> Telefone
                  </dt>
                  <dd>{detalhe.telefone ?? detalhe.celular ?? "—"}</dd>
                </div>
              </dl>

              {detalhe.historico_medico_visivel && gruposCid.length > 0 ? (
                <div className="alerta-cid">
                  <div className="alerta-cid__cabecalho">
                    <span aria-hidden="true">!</span>
                    <div>
                      <h3>Grupos de CID em atenção</h3>
                      <p>Dias de atestado acumulados por código</p>
                    </div>
                    <span className="etiqueta-alerta">{gruposCid.length} alerta(s)</span>
                  </div>
                  <div className="alerta-cid__grupos">
                    {gruposCid.map((grupo) => (
                      <article className="alerta-cid__grupo" key={grupo.codigo}>
                        <b>{grupo.codigo}</b>
                        <strong>
                          {grupo.dias}
                          <small> dias</small>
                        </strong>
                      </article>
                    ))}
                  </div>
                </div>
              ) : null}

              {detalhe.historico_medico_visivel && detalhe.pericias.length > 0 ? (
                <>
                  <div className="abas-modal">
                    <button
                      type="button"
                      className={aba === "linha" ? "ativo" : ""}
                      onClick={() => setAba("linha")}
                    >
                      Linha do tempo <span>{detalhe.pericias.length}</span>
                    </button>
                    <button
                      type="button"
                      className={aba === "grafico" ? "ativo" : ""}
                      onClick={() => setAba("grafico")}
                    >
                      Análise gráfica <span>{gruposCid.length}</span>
                    </button>
                  </div>

                  {aba === "linha" ? (
                    <ol className="linha-do-tempo">
                      {detalhe.pericias.map((pericia) => {
                        const subtitulo = pericia.atestado
                          ? `Atestado · ${pericia.dias_atestado ?? "?"} dia(s)`
                          : (pericia.conduta ??
                            pericia.subjetivo ??
                            pericia.objetivo ??
                            pericia.relatorio ??
                            "Sem detalhes adicionais");
                        return (
                          <li key={pericia.id}>
                            <span
                              className={`linha-do-tempo__marca${pericia.atestado ? " linha-do-tempo__marca--atestado" : ""}`}
                              aria-hidden="true"
                            />
                            <time>{formatarData(pericia.data)}</time>
                            <div className="linha-do-tempo__conteudo">
                              <span
                                className={`linha-do-tempo__tag${pericia.atestado ? " linha-do-tempo__tag--atestado" : ""}`}
                              >
                                {pericia.atestado ? "Atestado" : "Consulta"}
                              </span>
                              <h4>
                                {pericia.cids[0] ? (
                                  <>
                                    <b>{pericia.cids[0]}</b> ·{" "}
                                  </>
                                ) : null}
                                {pericia.motivo ?? "Perícia médica"}
                              </h4>
                              <p className="linha-do-tempo__subtitulo">{subtitulo}</p>
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  ) : (
                    <div className="grafico-barras">
                      {gruposCid.length === 0 ? (
                        <p>Sem grupos de CID registrados.</p>
                      ) : (
                        gruposCid.map((grupo) => (
                          <div className="grafico-barras__linha" key={grupo.codigo}>
                            <b>{grupo.codigo}</b>
                            <span className="grafico-barras__trilha">
                              <span
                                style={{
                                  width: `${Math.round((grupo.dias / maiorDiasPorCid) * 100)}%`,
                                }}
                              />
                            </span>
                            <strong>{grupo.dias}d</strong>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </>
              ) : null}
            </div>

            <aside className="prontuario-lateral">
              <div className="resumo-card">
                <p className="sobretitulo">Resumo · 60 dias</p>
                <div className="resumo-card__grade">
                  <span>
                    <strong>{protocolosUltimos60Dias.length}</strong>
                    <small>protocolo(s)</small>
                  </span>
                  {detalhe.historico_medico_visivel ? (
                    <>
                      <span>
                        <strong>{periciasUltimos60Dias.length}</strong>
                        <small>registro(s)</small>
                      </span>
                      <span>
                        <strong>{diasDeAtestado60Dias}</strong>
                        <small>dia(s) atestado</small>
                      </span>
                    </>
                  ) : null}
                </div>
              </div>

              {detalhe.historico_medico_visivel ? (
                <SecaoParecer
                  servidorSismedId={detalhe.id}
                  permissoes={permissoes}
                  usuarioId={usuarioId}
                />
              ) : null}

              {detalhe.historico_medico_visivel ? (
                <SecaoApoio servidorSismedId={detalhe.id} permissoes={permissoes} />
              ) : null}
            </aside>
          </div>
        ) : null}
      </section>
    </div>
  );
}

function SecaoParecer({
  servidorSismedId,
  permissoes,
  usuarioId,
}: {
  servidorSismedId: number;
  permissoes: string[];
  usuarioId: number;
}) {
  const [pareceres, setPareceres] = useState<Parecer[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [editando, setEditando] = useState<Parecer | null>(null);
  const podeAlterar = permissoes.includes("alterar_conteudo_medico");

  function recarregar() {
    setCarregando(true);
    listarPareceres(servidorSismedId)
      .then((resultado) => {
        setPareceres(resultado);
        setErro(null);
      })
      .catch((error: unknown) => setErro(mensagemDoErro(error)))
      .finally(() => setCarregando(false));
  }

  useEffect(() => {
    let ativo = true;
    listarPareceres(servidorSismedId)
      .then((resultado) => {
        if (!ativo) return;
        setPareceres(resultado);
        setErro(null);
      })
      .catch((error: unknown) => {
        if (ativo) setErro(mensagemDoErro(error));
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [servidorSismedId]);

  return (
    <div className="secao-parecer">
      <h3>Pareceres</h3>

      {carregando ? (
        <div className="estado-painel" aria-live="polite">
          <span className="carregando-indicador" aria-hidden="true" />
          <p>Carregando pareceres…</p>
        </div>
      ) : null}

      {erro ? (
        <p className="mensagem-erro" role="alert">
          {erro}
        </p>
      ) : null}

      {!carregando && !erro && pareceres.length === 0 ? (
        <p className="texto-secundario">Nenhum parecer registrado.</p>
      ) : null}

      {!carregando && pareceres.length > 0 ? (
        <ul className="lista-pareceres">
          {pareceres.map((parecer) => (
            <li key={parecer.id}>
              <div className="lista-pareceres__cabecalho">
                <span>
                  {parecer.autor} · {formatarData(parecer.criado_em.slice(0, 10))}
                </span>
                <span
                  className={`etiqueta-estado${parecer.estado === "concluido" ? " etiqueta-estado--concluido" : ""}`}
                >
                  {parecer.estado_descricao}
                </span>
              </div>
              <p className="lista-pareceres__texto">{parecer.texto}</p>
              <div className="lista-pareceres__rodape">
                <span className="etiqueta-situacao">{parecer.conclusao_descricao}</span>
                {parecer.prioritario ? (
                  <span className="etiqueta-alerta">Prioritário</span>
                ) : null}
                {podeAlterar &&
                parecer.estado === "rascunho" &&
                parecer.autor_id === usuarioId ? (
                  <div className="lista-pareceres__acoes">
                    <button type="button" onClick={() => setEditando(parecer)}>
                      Editar
                    </button>
                    <button
                      type="button"
                      onClick={() => void concluirParecer(parecer.id).then(recarregar)}
                    >
                      Concluir
                    </button>
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {podeAlterar ? (
        <FormularioParecer
          key={editando?.id ?? "novo"}
          servidorSismedId={servidorSismedId}
          parecer={editando}
          aoSalvar={() => {
            setEditando(null);
            recarregar();
          }}
          aoCancelarEdicao={() => setEditando(null)}
        />
      ) : null}
    </div>
  );
}

function FormularioParecer({
  servidorSismedId,
  parecer,
  aoSalvar,
  aoCancelarEdicao,
}: {
  servidorSismedId: number;
  parecer: Parecer | null;
  aoSalvar: () => void;
  aoCancelarEdicao: () => void;
}) {
  const [texto, setTexto] = useState(parecer?.texto ?? "");
  const [conclusao, setConclusao] = useState(parecer?.conclusao ?? "acompanhamento");
  const [prioritario, setPrioritario] = useState(parecer?.prioritario ?? false);
  const [dataReavaliacao, setDataReavaliacao] = useState(parecer?.data_reavaliacao ?? "");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar(concluir: boolean) {
    if (!texto.trim()) {
      setErro("Descreva o parecer antes de salvar.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      const dados = {
        texto,
        conclusao,
        prioritario,
        data_reavaliacao: dataReavaliacao || null,
      };
      if (parecer) {
        await editarParecer(parecer.id, dados);
        if (concluir) await concluirParecer(parecer.id);
      } else {
        await criarParecer(servidorSismedId, dados, concluir);
      }
      aoSalvar();
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form
      className="formulario-parecer"
      onSubmit={(event) => {
        event.preventDefault();
        void enviar(false);
      }}
    >
      <p className="sobretitulo">{parecer ? "Editar parecer" : "Novo parecer"}</p>
      <label>
        Parecer médico
        <textarea
          value={texto}
          onChange={(event) => setTexto(event.target.value)}
          placeholder="Descreva a avaliação clínica, orientações e conduta…"
          rows={5}
        />
      </label>
      <label>
        Conclusão / andamento
        <select value={conclusao} onChange={(event) => setConclusao(event.target.value)}>
          {CONCLUSOES_DO_PARECER.map((opcao) => (
            <option key={opcao.valor} value={opcao.valor}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
      </label>
      <label>
        Reavaliação
        <input
          type="date"
          value={dataReavaliacao ?? ""}
          onChange={(event) => setDataReavaliacao(event.target.value)}
        />
      </label>
      <label className="linha-checagem">
        <input
          type="checkbox"
          checked={prioritario}
          onChange={(event) => setPrioritario(event.target.checked)}
        />
        Sinalizar para acompanhamento prioritário
      </label>
      {erro ? (
        <p className="mensagem-erro" role="alert">
          {erro}
        </p>
      ) : null}
      <div className="formulario-parecer__acoes">
        <button
          type="button"
          className="botao botao--primario"
          disabled={enviando}
          onClick={() => void enviar(true)}
        >
          {parecer ? "Salvar e concluir" : "Registrar e concluir"}
        </button>
        <button
          type="button"
          className="botao botao--secundario"
          disabled={enviando}
          onClick={() => void enviar(false)}
        >
          Salvar rascunho
        </button>
        {parecer ? (
          <button type="button" className="botao botao--secundario" onClick={aoCancelarEdicao}>
            Cancelar
          </button>
        ) : null}
      </div>
    </form>
  );
}

const ESPECIALIDADES_DE_APOIO: { valor: Especialidade; rotulo: string }[] = [
  { valor: "neuropsicologia", rotulo: "Neuropsicólogo" },
  { valor: "assistencia_social", rotulo: "Assistente Social" },
  { valor: "seguranca_trabalho", rotulo: "Segurança do Trabalho" },
];

function SecaoApoio({
  servidorSismedId,
  permissoes,
}: {
  servidorSismedId: number;
  permissoes: string[];
}) {
  const [solicitacoes, setSolicitacoes] = useState<SolicitacaoApoio[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const podeSolicitar = permissoes.includes("solicitar_apoio_especializado");

  function recarregar() {
    setCarregando(true);
    listarSolicitacoesDoServidor(servidorSismedId)
      .then((resultado) => {
        setSolicitacoes(resultado);
        setErro(null);
      })
      .catch((error: unknown) => setErro(mensagemDoErro(error)))
      .finally(() => setCarregando(false));
  }

  useEffect(() => {
    let ativo = true;
    listarSolicitacoesDoServidor(servidorSismedId)
      .then((resultado) => {
        if (!ativo) return;
        setSolicitacoes(resultado);
        setErro(null);
      })
      .catch((error: unknown) => {
        if (ativo) setErro(mensagemDoErro(error));
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [servidorSismedId]);

  return (
    <div className="secao-apoio">
      <h3>Apoio multidisciplinar</h3>

      {carregando ? (
        <div className="estado-painel" aria-live="polite">
          <span className="carregando-indicador" aria-hidden="true" />
          <p>Carregando solicitações de apoio…</p>
        </div>
      ) : null}

      {erro ? (
        <p className="mensagem-erro" role="alert">
          {erro}
        </p>
      ) : null}

      {!carregando && !erro && solicitacoes.length === 0 ? (
        <p className="texto-secundario">Nenhuma solicitação de apoio registrada.</p>
      ) : null}

      {!carregando && solicitacoes.length > 0 ? (
        <ul className="lista-solicitacoes-apoio">
          {solicitacoes.map((solicitacao) => (
            <li key={solicitacao.id}>
              <div className="lista-solicitacoes-apoio__cabecalho">
                <span>
                  {solicitacao.especialidade_descricao} · solicitado por{" "}
                  {solicitacao.solicitante}
                </span>
                <span
                  className={`etiqueta-estado${solicitacao.estado === "respondida" ? " etiqueta-estado--concluido" : ""}`}
                >
                  {solicitacao.estado_descricao}
                </span>
              </div>
              <p className="lista-solicitacoes-apoio__texto">
                {solicitacao.texto_solicitacao}
              </p>
              {solicitacao.estado === "respondida" ? (
                <div className="lista-solicitacoes-apoio__resposta">
                  <span>{solicitacao.respondente} respondeu</span>
                  <p>{solicitacao.texto_resposta}</p>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}

      {podeSolicitar ? (
        <FormularioSolicitacaoApoio
          servidorSismedId={servidorSismedId}
          aoSalvar={recarregar}
        />
      ) : null}
    </div>
  );
}

function FormularioSolicitacaoApoio({
  servidorSismedId,
  aoSalvar,
}: {
  servidorSismedId: number;
  aoSalvar: () => void;
}) {
  const [especialidade, setEspecialidade] = useState<Especialidade>(
    ESPECIALIDADES_DE_APOIO[0].valor,
  );
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar() {
    if (!texto.trim()) {
      setErro("Descreva o motivo da solicitação antes de enviar.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      await criarSolicitacao({
        servidor_sismed_id: servidorSismedId,
        especialidade,
        texto_solicitacao: texto,
      });
      setTexto("");
      aoSalvar();
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form
      className="formulario-solicitacao-apoio"
      onSubmit={(event) => {
        event.preventDefault();
        void enviar();
      }}
    >
      <p className="sobretitulo">Solicitar apoio</p>
      <label>
        Especialidade
        <select
          value={especialidade}
          onChange={(event) => setEspecialidade(event.target.value as Especialidade)}
        >
          {ESPECIALIDADES_DE_APOIO.map((opcao) => (
            <option key={opcao.valor} value={opcao.valor}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
      </label>
      <label>
        Motivo da solicitação
        <textarea
          value={texto}
          onChange={(event) => setTexto(event.target.value)}
          placeholder="Descreva o que precisa ser avaliado…"
          rows={4}
        />
      </label>
      {erro ? (
        <p className="mensagem-erro" role="alert">
          {erro}
        </p>
      ) : null}
      <button type="submit" className="botao botao--primario" disabled={enviando}>
        Enviar solicitação
      </button>
    </form>
  );
}

function iniciais(nome: string): string {
  return nome
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte.charAt(0))
    .join("")
    .toUpperCase();
}

function formatarData(data: string | null): string {
  if (!data) return "—";
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(
    new Date(`${data}T00:00:00Z`),
  );
}

function dentroDosUltimos60Dias(data: string | null): boolean {
  if (!data) return false;
  const limite = new Date();
  limite.setUTCDate(limite.getUTCDate() - 60);
  return new Date(`${data}T00:00:00Z`) >= limite;
}

function mensagemDoErro(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a operação.";
}
