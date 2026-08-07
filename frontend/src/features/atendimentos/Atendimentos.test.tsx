import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Atendimentos } from "./Atendimentos";

const permissoesEspecialista = ["responder_solicitacao_apoio"];
const permissoesMedico = ["solicitar_apoio_especializado"];
const usuarioIdPadrao = 1;

const solicitacaoPendente = {
  id: 1,
  servidor_sismed_id: 1001,
  protocolo_sismed_id: null,
  especialidade: "seguranca_trabalho",
  especialidade_descricao: "Segurança do Trabalho",
  solicitante: "Ana Souza",
  solicitante_id: 2,
  unidade: "Medicina do Trabalho",
  texto_solicitacao: "Avaliar risco ergonômico do posto de trabalho.",
  estado: "aberta",
  estado_descricao: "Aguardando resposta",
  respondente: null,
  texto_resposta: "",
  criado_em: "2026-07-01T10:00:00Z",
  respondido_em: null,
  servidor_nome: "Maria da Silva",
};

const atendimentoAberto = {
  servidor_sismed_id: 1001,
  servidor_nome: "Maria da Silva",
  situacao_protocolo: "Em analise",
  parecer_em_aberto: true,
  parecer_autor: "Ana Souza",
  apoios: [
    {
      especialidade: "seguranca_trabalho",
      especialidade_descricao: "Segurança do Trabalho",
      estado: "aberta",
      estado_descricao: "Aguardando resposta",
    },
    {
      especialidade: "assistencia_social",
      especialidade_descricao: "Assistente Social",
      estado: "respondida",
      estado_descricao: "Respondida",
    },
  ],
  ultima_atividade_em: "2026-07-01T10:00:00Z",
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

describe("Atendimentos — fila do especialista", () => {
  it("mostra estado vazio quando não há solicitações pendentes", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta(200, [])));

    render(<Atendimentos permissoes={permissoesEspecialista} usuarioId={usuarioIdPadrao} />);

    expect(
      await screen.findByText("Nenhuma solicitação pendente para você no momento."),
    ).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando a API falha", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(403, { detail: "Sem permissão." })),
    );

    render(<Atendimentos permissoes={permissoesEspecialista} usuarioId={usuarioIdPadrao} />);

    expect(await screen.findByText("Sem permissão.")).toBeInTheDocument();
  });

  it("lista as solicitações pendentes com o nome do servidor", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, [solicitacaoPendente])),
    );

    render(<Atendimentos permissoes={permissoesEspecialista} usuarioId={usuarioIdPadrao} />);

    expect(await screen.findByText("Maria da Silva")).toBeInTheDocument();
    expect(screen.getByText("Ana Souza")).toBeInTheDocument();
    expect(
      screen.getByText("Avaliar risco ergonômico do posto de trabalho."),
    ).toBeInTheDocument();
  });

  it("responde a uma solicitação e recarrega a fila", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [solicitacaoPendente]))
      .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-teste" }))
      .mockResolvedValueOnce(
        resposta(200, { ...solicitacaoPendente, estado: "respondida" }),
      )
      .mockResolvedValueOnce(resposta(200, []));
    vi.stubGlobal("fetch", fetchMock);

    render(<Atendimentos permissoes={permissoesEspecialista} usuarioId={usuarioIdPadrao} />);

    fireEvent.click(await screen.findByRole("button", { name: "Responder" }));
    fireEvent.change(
      await screen.findByPlaceholderText(/Descreva a avaliação e as recomendações/),
      { target: { value: "Posto avaliado, sem risco relevante." } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Enviar resposta" }));

    expect(
      await screen.findByText("Nenhuma solicitação pendente para você no momento."),
    ).toBeInTheDocument();
    const chamadaDeResposta = fetchMock.mock.calls.find((chamada: unknown[]) =>
      String(chamada[0]).includes("/responder"),
    );
    expect(chamadaDeResposta).toBeDefined();
  });
});

describe("Atendimentos — atendimentos do médico", () => {
  it("mostra estado vazio quando não há atendimentos em andamento", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta(200, [])));

    render(<Atendimentos permissoes={permissoesMedico} usuarioId={usuarioIdPadrao} />);

    expect(
      await screen.findByText(
        "Nenhum atendimento em andamento. Os concluídos ficam no histórico da Consulta.",
      ),
    ).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando a API falha", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(403, { detail: "Sem permissão." })),
    );

    render(<Atendimentos permissoes={permissoesMedico} usuarioId={usuarioIdPadrao} />);

    expect(await screen.findByText("Sem permissão.")).toBeInTheDocument();
  });

  it("lista os atendimentos em andamento com o status do parecer e das solicitações", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, [atendimentoAberto])),
    );

    render(<Atendimentos permissoes={permissoesMedico} usuarioId={usuarioIdPadrao} />);

    expect(await screen.findByText("Maria da Silva")).toBeInTheDocument();
    expect(screen.getByText("Em analise")).toBeInTheDocument();
    expect(screen.getByText("Em rascunho")).toBeInTheDocument();
    expect(screen.getByText("Ana Souza")).toBeInTheDocument();
    expect(
      screen.getByText("Segurança do Trabalho: Aguardando resposta"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Assistente Social: Respondida"),
    ).toBeInTheDocument();
  });

  it("abre o prontuário do servidor ao clicar em Abrir prontuário", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [atendimentoAberto]))
      .mockResolvedValueOnce(
        resposta(200, {
          id: 1001,
          nome: "Maria da Silva",
          nome_social: null,
          cpf: "123.456.789-00",
          email: "maria@example.test",
          ativo: true,
          admissao: "2020-01-01",
          tramitacao: null,
          nascimento: null,
          telefone: null,
          celular: null,
          protocolos: [],
          historico_medico_visivel: false,
          pericias: [],
          atendimentos: [],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<Atendimentos permissoes={permissoesMedico} usuarioId={usuarioIdPadrao} />);

    fireEvent.click(await screen.findByRole("button", { name: /Abrir prontuário/ }));

    expect(await screen.findByText("maria@example.test")).toBeInTheDocument();
  });
});
