import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PainelIndicadores } from "./PainelIndicadores";

const indicadores = {
  servidores_acompanhados: 4,
  pericias_60_dias: 13,
  pareceres_em_rascunho: 2,
  pericias_com_atestado_60_dias: 5,
  grupos_cid: [
    { codigo: "Z00.0", ocorrencias: 10 },
    { codigo: "M54.5", ocorrencias: 2 },
    { codigo: "R50.9", ocorrencias: 1 },
  ],
  solicitacoes_apoio_abertas: 3,
  minhas_solicitacoes_pendentes: null,
};

function resposta(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("PainelIndicadores", () => {
  it("mostra os cartões com os números vindos da API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, indicadores)),
    );

    render(<PainelIndicadores nomeUsuario="Ana" permissoes={[]} />);

    expect(await screen.findByText("4")).toBeInTheDocument();
    expect(screen.getByText("13")).toBeInTheDocument();
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(
      screen.getByText("2 parecer(es) em rascunho aguardando conclusão."),
    ).toBeInTheDocument();
  });

  it("mostra o gráfico de barras e a legenda da rosca de CID", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, indicadores)),
    );

    render(<PainelIndicadores nomeUsuario="Ana" permissoes={[]} />);

    expect((await screen.findAllByText("Z00.0")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("M54.5").length).toBeGreaterThan(0);
    expect(screen.getAllByText("R50.9").length).toBeGreaterThan(0);
    expect(screen.getByText("Distribuição de CIDs")).toBeInTheDocument();
  });

  it("mostra mensagem neutra quando não há pareceres em rascunho", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        resposta(200, { ...indicadores, pareceres_em_rascunho: 0 }),
      ),
    );

    render(<PainelIndicadores nomeUsuario="Ana" permissoes={[]} />);

    expect(
      await screen.findByText("Nenhum parecer pendente de conclusão."),
    ).toBeInTheDocument();
  });

  it("informa quando os indicadores não podem ser carregados", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(500, { detail: "Erro interno." })),
    );

    render(<PainelIndicadores nomeUsuario="Ana" permissoes={[]} />);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("não mostra o cartão de pendências quando o perfil não solicita nem responde apoio", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, indicadores)),
    );

    render(<PainelIndicadores nomeUsuario="Ana" permissoes={[]} />);

    await screen.findByText("Solicitações de apoio abertas");
    expect(screen.queryByText("Solicitações pendentes para você")).toBeNull();
    expect(
      screen.queryByText("Suas solicitações aguardando resposta"),
    ).toBeNull();
  });

  it("mostra o cartão de solicitações pendentes e navega para Atendimentos ao clicar", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        resposta(200, { ...indicadores, minhas_solicitacoes_pendentes: 2 }),
      ),
    );
    const aoAbrirAtendimentos = vi.fn();

    render(
      <PainelIndicadores
        nomeUsuario="Ana"
        permissoes={["responder_solicitacao_apoio"]}
        aoAbrirAtendimentos={aoAbrirAtendimentos}
      />,
    );

    fireEvent.click(
      await screen.findByText("Solicitações pendentes para você"),
    );

    expect(aoAbrirAtendimentos).toHaveBeenCalledTimes(1);
  });

  it("mostra o rótulo de solicitante para quem só solicita apoio", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        resposta(200, { ...indicadores, minhas_solicitacoes_pendentes: 1 }),
      ),
    );

    render(
      <PainelIndicadores
        nomeUsuario="Ana"
        permissoes={["solicitar_apoio_especializado"]}
      />,
    );

    expect(
      await screen.findByText("Suas solicitações aguardando resposta"),
    ).toBeInTheDocument();
  });
});
