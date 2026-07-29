import { useEffect, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { consultarIndicadores, GrupoCidIndicador, Indicadores } from "./api";

const PALETA_CID = [
  "var(--blue)",
  "var(--green)",
  "var(--amber)",
  "#7652ae",
  "var(--red)",
  "var(--cyan)",
];

export function PainelIndicadores({ nomeUsuario }: { nomeUsuario: string }) {
  const [indicadores, setIndicadores] = useState<Indicadores | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    consultarIndicadores()
      .then((resultado) => {
        if (!ativo) return;
        setIndicadores(resultado);
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
  }, []);

  if (carregando) {
    return (
      <div className="estado-painel" aria-live="polite">
        <span className="carregando-indicador" aria-hidden="true" />
        <p>Carregando indicadores…</p>
      </div>
    );
  }

  if (erro || !indicadores) {
    return (
      <div className="estado-painel">
        <p className="mensagem-erro" role="alert">
          {erro ?? "Não foi possível carregar os indicadores."}
        </p>
      </div>
    );
  }

  const maiorOcorrencia = Math.max(
    1,
    ...indicadores.grupos_cid.map((grupo) => grupo.ocorrencias),
  );
  const totalOcorrencias = indicadores.grupos_cid.reduce(
    (total, grupo) => total + grupo.ocorrencias,
    0,
  );

  return (
    <div className="painel-indicadores">
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Painel gerencial</p>
          <h1>Visão geral</h1>
          <p>Indicadores dos últimos 60 dias.</p>
        </div>
        <span className="data-atual">● Dados atualizados agora</span>
      </header>

      <section className="painel painel--boas-vindas">
        <div>
          <p className="sobretitulo">☀ Bom dia, {nomeUsuario}</p>
          <h2>
            {indicadores.pareceres_em_rascunho > 0
              ? `${indicadores.pareceres_em_rascunho} parecer(es) em rascunho aguardando conclusão.`
              : "Nenhum parecer pendente de conclusão."}
          </h2>
          <p>Acompanhe os servidores e registre pareceres pela Consulta.</p>
        </div>
      </section>

      <section className="grade-indicadores" aria-label="Indicadores gerais">
        <CartaoIndicador
          tom="azul"
          icone="◎"
          valor={String(indicadores.servidores_acompanhados)}
          rotulo="Servidores acompanhados"
          detalhe="Com parecer registrado"
        />
        <CartaoIndicador
          tom="verde"
          icone="✓"
          valor={String(indicadores.pericias_60_dias)}
          rotulo="Perícias em 60 dias"
          detalhe="Em todo o sistema"
        />
        <CartaoIndicador
          tom="amarelo"
          icone="◷"
          valor={String(indicadores.pareceres_em_rascunho)}
          rotulo="Pareceres em rascunho"
          detalhe="Aguardando conclusão"
        />
        <CartaoIndicador
          tom="roxo"
          icone="✎"
          valor={String(indicadores.pericias_com_atestado_60_dias)}
          rotulo="Perícias com atestado"
          detalhe="Últimos 60 dias"
        />
      </section>

      <section className="indicadores-graficos">
        <article className="grafico-barras">
          <p className="sobretitulo">Ocorrências por grupo de CID</p>
          {indicadores.grupos_cid.length === 0 ? (
            <p className="texto-secundario">
              Nenhuma ocorrência registrada nos últimos 60 dias.
            </p>
          ) : (
            indicadores.grupos_cid.map((grupo) => (
              <div className="grafico-barras__linha" key={grupo.codigo}>
                <b>{grupo.codigo}</b>
                <span className="grafico-barras__trilha">
                  <span
                    style={{
                      width: `${Math.round((grupo.ocorrencias / maiorOcorrencia) * 100)}%`,
                    }}
                  />
                </span>
                <strong>{grupo.ocorrencias}</strong>
              </div>
            ))
          )}
        </article>

        <article className="rosca-cid">
          <p className="sobretitulo">Distribuição de CIDs</p>
          {indicadores.grupos_cid.length === 0 ? (
            <p className="texto-secundario">Sem dados suficientes.</p>
          ) : (
            <div className="rosca-cid__corpo">
              <div
                className="rosca-cid__grafico"
                style={{ background: montarGradienteRosca(indicadores.grupos_cid, totalOcorrencias) }}
              />
              <ul className="rosca-cid__legenda">
                {indicadores.grupos_cid.map((grupo, indice) => (
                  <li key={grupo.codigo}>
                    <i style={{ background: corDaFatia(indice) }} aria-hidden="true" />
                    <span>{grupo.codigo}</span>
                    <small>{grupo.ocorrencias}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </article>
      </section>
    </div>
  );
}

function CartaoIndicador({
  tom,
  icone,
  valor,
  rotulo,
  detalhe,
}: {
  tom: string;
  icone: string;
  valor: string;
  rotulo: string;
  detalhe: string;
}) {
  return (
    <article className={`cartao-indicador cartao-indicador--${tom}`}>
      <span className="cartao-indicador__icone" aria-hidden="true">
        {icone}
      </span>
      <div>
        <strong>{valor}</strong>
        <h2>{rotulo}</h2>
        <p>{detalhe}</p>
      </div>
    </article>
  );
}

function corDaFatia(indice: number): string {
  return PALETA_CID[indice % PALETA_CID.length];
}

function montarGradienteRosca(grupos: GrupoCidIndicador[], total: number): string {
  if (total === 0) return "var(--line)";
  let acumulado = 0;
  const partes = grupos.map((grupo, indice) => {
    const inicio = (acumulado / total) * 360;
    acumulado += grupo.ocorrencias;
    const fim = (acumulado / total) * 360;
    return `${corDaFatia(indice)} ${inicio}deg ${fim}deg`;
  });
  return `conic-gradient(${partes.join(", ")})`;
}

function mensagemDoErro(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a operação.";
}
