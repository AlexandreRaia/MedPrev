import { useEffect, useState } from "react";

import {
  AtendimentoAberto,
  listarAtendimentos,
  listarMinhasSolicitacoes,
  MinhaSolicitacaoApoio,
  responderSolicitacao,
} from "../apoio/api";
import { DetalheServidorModal } from "../legado/Servidores";
import { ApiError } from "../../shared/api/client";

export function Atendimentos({
  permissoes,
  usuarioId,
}: {
  permissoes: string[];
  usuarioId: number;
}) {
  if (permissoes.includes("responder_solicitacao_apoio")) {
    return <FilaDeSolicitacoes />;
  }
  if (permissoes.includes("solicitar_apoio_especializado")) {
    return <AtendimentosDaUnidade permissoes={permissoes} usuarioId={usuarioId} />;
  }
  return null;
}

function AtendimentosDaUnidade({
  permissoes,
  usuarioId,
}: {
  permissoes: string[];
  usuarioId: number;
}) {
  const [atendimentos, setAtendimentos] = useState<AtendimentoAberto[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [servidorSelecionado, setServidorSelecionado] = useState<number | null>(null);

  useEffect(() => {
    const controlador = new AbortController();
    listarAtendimentos(controlador.signal)
      .then((resultado) => {
        setAtendimentos(resultado);
        setErro(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setErro(mensagemDoErro(error));
      })
      .finally(() => setCarregando(false));
    return () => controlador.abort();
  }, []);

  return (
    <>
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Atendimentos</p>
          <h1>Atendimentos em andamento</h1>
          <p>
            Casos da sua unidade com parecer em rascunho ou solicitação de apoio pendente —
            de qualquer colega, não só os seus.
          </p>
        </div>
      </header>
      <section className="painel">
        {erro ? (
          <p className="mensagem-erro" role="alert">
            {erro}
          </p>
        ) : null}

        {carregando ? (
          <div className="estado-painel" aria-live="polite">
            <span className="carregando-indicador" aria-hidden="true" />
            <p>Carregando atendimentos…</p>
          </div>
        ) : null}

        {!carregando && !erro && atendimentos.length === 0 ? (
          <div className="estado-painel">
            <p>Nenhum atendimento em andamento. Os concluídos ficam no histórico da Consulta.</p>
          </div>
        ) : null}

        {!carregando && atendimentos.length > 0 ? (
          <div className="tabela-responsiva">
            <table>
              <thead>
                <tr>
                  <th>Servidor</th>
                  <th>Parecer</th>
                  <th>Apoio solicitado</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {atendimentos.map((atendimento) => (
                  <tr key={atendimento.servidor_sismed_id}>
                    <td>
                      <strong>{atendimento.servidor_nome ?? "Servidor não encontrado"}</strong>{" "}
                      <span className="codigo-prontuario">
                        P{atendimento.servidor_sismed_id}
                      </span>
                      {atendimento.situacao_protocolo ? (
                        <>
                          {" "}
                          <span className="etiqueta-situacao">
                            {atendimento.situacao_protocolo}
                          </span>
                        </>
                      ) : null}
                    </td>
                    <td>
                      {atendimento.parecer_em_aberto ? (
                        <>
                          <span className="etiqueta-estado">Em rascunho</span>{" "}
                          <span className="texto-secundario">{atendimento.parecer_autor}</span>
                        </>
                      ) : (
                        <span className="texto-secundario">Sem parecer aberto</span>
                      )}
                    </td>
                    <td>
                      {atendimento.apoios.length === 0 ? (
                        <span className="texto-secundario">Nenhuma</span>
                      ) : (
                        <div className="lista-chips-apoio">
                          {atendimento.apoios.map((apoio) => (
                            <span
                              key={apoio.especialidade}
                              className={
                                apoio.estado === "respondida"
                                  ? "etiqueta-estado etiqueta-estado--concluido"
                                  : "etiqueta-estado"
                              }
                            >
                              {apoio.especialidade_descricao}: {apoio.estado_descricao}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="celula-acao">
                      <button
                        className="botao-historico"
                        type="button"
                        onClick={() => setServidorSelecionado(atendimento.servidor_sismed_id)}
                      >
                        <span aria-hidden="true">☰</span> Abrir prontuário
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {servidorSelecionado !== null ? (
        <DetalheServidorModal
          key={servidorSelecionado}
          servidorId={servidorSelecionado}
          permissoes={permissoes}
          usuarioId={usuarioId}
          aoFechar={() => setServidorSelecionado(null)}
        />
      ) : null}
    </>
  );
}

function FilaDeSolicitacoes() {
  const [solicitacoes, setSolicitacoes] = useState<MinhaSolicitacaoApoio[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [selecionada, setSelecionada] = useState<MinhaSolicitacaoApoio | null>(null);

  function recarregar() {
    setCarregando(true);
    listarMinhasSolicitacoes()
      .then((resultado) => {
        setSolicitacoes(resultado);
        setErro(null);
      })
      .catch((error: unknown) => setErro(mensagemDoErro(error)))
      .finally(() => setCarregando(false));
  }

  useEffect(() => {
    const controlador = new AbortController();
    listarMinhasSolicitacoes(controlador.signal)
      .then((resultado) => {
        setSolicitacoes(resultado);
        setErro(null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setErro(mensagemDoErro(error));
      })
      .finally(() => setCarregando(false));
    return () => controlador.abort();
  }, []);

  return (
    <>
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Atendimentos</p>
          <h1>Solicitações de apoio</h1>
          <p>Pedidos de apoio direcionados à sua especialidade.</p>
        </div>
      </header>
      <section className="painel">
        {erro ? (
          <p className="mensagem-erro" role="alert">
            {erro}
          </p>
        ) : null}

        {carregando ? (
          <div className="estado-painel" aria-live="polite">
            <span className="carregando-indicador" aria-hidden="true" />
            <p>Carregando solicitações…</p>
          </div>
        ) : null}

        {!carregando && !erro && solicitacoes.length === 0 ? (
          <div className="estado-painel">
            <p>Nenhuma solicitação pendente para você no momento.</p>
          </div>
        ) : null}

        {!carregando && solicitacoes.length > 0 ? (
          <div className="tabela-responsiva">
            <table>
              <thead>
                <tr>
                  <th>Servidor</th>
                  <th>Solicitante</th>
                  <th>Motivo</th>
                  <th aria-label="Ações" />
                </tr>
              </thead>
              <tbody>
                {solicitacoes.map((solicitacao) => (
                  <tr key={solicitacao.id}>
                    <td>
                      <strong>{solicitacao.servidor_nome ?? "Servidor não encontrado"}</strong>{" "}
                      <span className="codigo-prontuario">P{solicitacao.servidor_sismed_id}</span>
                    </td>
                    <td>{solicitacao.solicitante}</td>
                    <td>{solicitacao.texto_solicitacao}</td>
                    <td className="celula-acao">
                      <button
                        className="botao-historico"
                        type="button"
                        onClick={() => setSelecionada(solicitacao)}
                      >
                        Responder
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {selecionada ? (
        <ModalResposta
          solicitacao={selecionada}
          aoFechar={() => setSelecionada(null)}
          aoResponder={() => {
            setSelecionada(null);
            recarregar();
          }}
        />
      ) : null}
    </>
  );
}

function ModalResposta({
  solicitacao,
  aoFechar,
  aoResponder,
}: {
  solicitacao: MinhaSolicitacaoApoio;
  aoFechar: () => void;
  aoResponder: () => void;
}) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function enviar() {
    if (!texto.trim()) {
      setErro("Descreva sua avaliação antes de enviar.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      await responderSolicitacao(solicitacao.id, texto);
      aoResponder();
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="modal-fundo" role="presentation">
      <section className="modal modal--compacto" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <h2>Responder solicitação</h2>
          <button className="fechar-modal" onClick={aoFechar} aria-label="Fechar">
            ×
          </button>
        </div>
        <p className="texto-secundario">
          {solicitacao.solicitante} solicitou apoio de{" "}
          {solicitacao.especialidade_descricao.toLowerCase()} para{" "}
          <strong>{solicitacao.servidor_nome ?? `servidor P${solicitacao.servidor_sismed_id}`}</strong>:
        </p>
        <p className="lista-solicitacoes-apoio__texto">{solicitacao.texto_solicitacao}</p>
        <form
          className="formulario-solicitacao-apoio"
          onSubmit={(event) => {
            event.preventDefault();
            void enviar();
          }}
        >
          <label>
            Sua avaliação
            <textarea
              value={texto}
              onChange={(event) => setTexto(event.target.value)}
              placeholder="Descreva a avaliação e as recomendações…"
              rows={5}
            />
          </label>
          {erro ? (
            <p className="mensagem-erro" role="alert">
              {erro}
            </p>
          ) : null}
          <button type="submit" className="botao botao--primario" disabled={enviando}>
            Enviar resposta
          </button>
        </form>
      </section>
    </div>
  );
}

function mensagemDoErro(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a operação.";
}
