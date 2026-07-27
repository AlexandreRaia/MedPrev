import { FormEvent, useEffect, useState } from "react";

import { ApiError } from "../../shared/api/client";
import {
  buscarServidores,
  consultarServidor,
  ServidorDetalhe,
  ServidorResumo,
} from "./api";

const TAMANHO_MINIMO_DA_BUSCA = 3;

export function Servidores() {
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
          <p>Localize um servidor por nome, nome social, CPF ou código.</p>
        </div>
      </header>
      <section className="painel">
        <form className="barra-filtros" onSubmit={submeterBusca}>
          <label className="campo-busca">
            <span>Buscar servidor</span>
            <input
              value={termo}
              onChange={(event) => setTermo(event.target.value)}
              placeholder="Digite ao menos 3 caracteres"
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
                  <th>Situação</th>
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
                      <span
                        className={`status status--${servidor.ativo ? "ativo" : "inativo"}`}
                      >
                        {servidor.ativo ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td className="celula-acao">
                      <button
                        className="link-tabela"
                        type="button"
                        onClick={() => setSelecionado(servidor.id)}
                      >
                        Ver histórico →
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
          aoFechar={() => setSelecionado(null)}
        />
      ) : null}
    </>
  );
}

function DetalheServidorModal({
  servidorId,
  aoFechar,
}: {
  servidorId: number;
  aoFechar: () => void;
}) {
  const [detalhe, setDetalhe] = useState<ServidorDetalhe | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

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

  return (
    <div className="modal-fundo" role="presentation">
      <section className="modal modal--prontuario" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <div className="prontuario-identidade">
            <span className="avatar avatar--prontuario" aria-hidden="true">
              {detalhe ? iniciais(nomeExibido) : ""}
            </span>
            <div>
              <p className="sobretitulo">Prontuário {detalhe ? `P${detalhe.id}` : ""}</p>
              <h2>{nomeExibido}</h2>
              {detalhe ? (
                <span
                  className={`indicador-status ${detalhe.ativo ? "indicador-status--ativo" : "indicador-status--inativo"}`}
                >
                  <i aria-hidden="true" />
                  Servidor {detalhe.ativo ? "ativo" : "inativo"}
                </span>
              ) : null}
            </div>
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

              {detalhe.historico_medico_visivel && detalhe.pericias.length > 0 ? (
                <>
                  <h3>Histórico clínico</h3>
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
                          <div className="linha-do-tempo__conteudo">
                            <time>{formatarData(pericia.data)}</time>
                            <h4>{pericia.motivo ?? "Perícia médica"}</h4>
                            <p className="linha-do-tempo__subtitulo">{subtitulo}</p>
                          </div>
                          <span
                            className={`linha-do-tempo__tag${pericia.atestado ? " linha-do-tempo__tag--atestado" : ""}`}
                          >
                            {pericia.atestado ? "Atestado" : "Consulta"}
                          </span>
                        </li>
                      );
                    })}
                  </ol>
                </>
              ) : null}
            </div>

            <aside className="prontuario-lateral">
              <p className="sobretitulo">Resumo</p>
              <div className="resumo-prontuario">
                <article className="resumo-prontuario__cartao resumo-prontuario__cartao--azul">
                  <span aria-hidden="true">▤</span>
                  <div>
                    <strong>{detalhe.protocolos.length}</strong>
                    <small>protocolo(s)</small>
                  </div>
                </article>
                {detalhe.historico_medico_visivel ? (
                  <article className="resumo-prontuario__cartao resumo-prontuario__cartao--roxo">
                    <span aria-hidden="true">✎</span>
                    <div>
                      <strong>{detalhe.pericias.length}</strong>
                      <small>registro(s) clínico(s)</small>
                    </div>
                  </article>
                ) : null}
              </div>
              <h3>Protocolos</h3>
              {detalhe.protocolos.length === 0 ? (
                <p>Nenhum protocolo registrado.</p>
              ) : (
                <ul className="lista-protocolos">
                  {detalhe.protocolos.map((protocolo) => (
                    <li key={protocolo.id}>
                      <time>{formatarData(protocolo.data)}</time>
                      <span className="etiqueta-situacao">
                        {protocolo.situacao ?? "—"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </aside>
          </div>
        ) : null}
      </section>
    </div>
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

function mensagemDoErro(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a operação.";
}
