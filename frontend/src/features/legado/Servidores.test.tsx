import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Servidores } from "./Servidores";

const permissoesSemAlterar = ["consultar_dados", "consultar_conteudo_medico"];
const permissoesComAlterar = [...permissoesSemAlterar, "alterar_conteudo_medico"];
const usuarioIdPadrao = 1;

function diasAtras(dias: number): string {
  const data = new Date();
  data.setUTCDate(data.getUTCDate() - dias);
  return data.toISOString().slice(0, 10);
}

const servidorResumo = {
  id: 1001,
  nome: "Maria da Silva",
  nome_social: null,
  cpf: "123.456.789-00",
  email: "maria@example.test",
  ativo: true,
  admissao: "2020-01-01",
  tramitacao: "Em andamento",
};

const servidorDetalheSemHistoricoMedico = {
  ...servidorResumo,
  nascimento: "1988-07-04",
  telefone: "1140000000",
  celular: "11999990000",
  protocolos: [{ id: 1, data: diasAtras(10), situacao: "Em andamento" }],
  historico_medico_visivel: false,
  pericias: [],
};

const servidorDetalheComHistoricoMedico = {
  ...servidorDetalheSemHistoricoMedico,
  historico_medico_visivel: true,
  pericias: [
    {
      id: 1,
      protocolo_id: 1,
      data: diasAtras(5),
      motivo: "Perícia médica de rotina",
      subjetivo: "Paciente relata dor lombar recorrente.",
      objetivo: "Exame clínico sem alterações agudas.",
      conduta: "Encaminhado para acompanhamento.",
      relatorio: null,
      atestado: true,
      dias_atestado: 15,
      cids: ["Z00.0"],
    },
    {
      id: 2,
      protocolo_id: 1,
      data: diasAtras(20),
      motivo: null,
      subjetivo: "Dor lombar recorrente.",
      objetivo: "Exame osteomuscular alterado.",
      conduta: "Encaminhado para fisioterapia.",
      relatorio: null,
      atestado: true,
      dias_atestado: 5,
      cids: ["Z00.0"],
    },
    {
      id: 3,
      protocolo_id: 1,
      data: diasAtras(30),
      motivo: null,
      subjetivo: "Consulta de rotina.",
      objetivo: "Sem alterações.",
      conduta: "Retorno em 30 dias.",
      relatorio: null,
      atestado: false,
      dias_atestado: null,
      cids: ["Z00.0"],
    },
  ],
};

const parecerConcluido = {
  id: 5,
  servidor_sismed_id: 1001,
  protocolo_sismed_id: null,
  autor: "Ana Souza",
  autor_id: 2,
  unidade: "Medicina do Trabalho",
  texto: "Paciente apto, sem restrições.",
  conclusao: "apto",
  conclusao_descricao: "Apto para o trabalho",
  estado: "concluido",
  estado_descricao: "Concluído",
  prioritario: false,
  data_reavaliacao: null,
  criado_em: "2026-07-01T10:00:00Z",
  atualizado_em: "2026-07-01T10:00:00Z",
  concluido_em: "2026-07-01T10:05:00Z",
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

async function abrirModal(
  fetchMock: ReturnType<typeof vi.fn>,
  permissoes: string[] = permissoesSemAlterar,
) {
  vi.stubGlobal("fetch", fetchMock);
  render(<Servidores permissoes={permissoes} usuarioId={usuarioIdPadrao} />);
  fireEvent.change(screen.getByPlaceholderText("Ex.: Maria da Silva, CPF ou P1001"), {
    target: { value: "Maria" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ver histórico" }));
}

describe("Servidores", () => {
  it("pede um termo de busca antes de consultar a API", () => {
    vi.stubGlobal("fetch", vi.fn());

    render(<Servidores permissoes={permissoesSemAlterar} usuarioId={usuarioIdPadrao} />);

    expect(
      screen.getByText("Digite um termo de busca para localizar um servidor."),
    ).toBeInTheDocument();
  });

  it("busca e lista os servidores encontrados", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, [servidorResumo])),
    );

    render(<Servidores permissoes={permissoesSemAlterar} usuarioId={usuarioIdPadrao} />);
    fireEvent.change(screen.getByPlaceholderText("Ex.: Maria da Silva, CPF ou P1001"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(await screen.findByText("Maria da Silva")).toBeInTheDocument();
    expect(
      screen.getByText(
        (_, elemento) => elemento?.textContent === "1 registro(s) encontrado(s)",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
  });

  it("busca pelo código do prontuário", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(resposta(200, [servidorResumo]));
    vi.stubGlobal("fetch", fetchMock);

    render(<Servidores permissoes={permissoesSemAlterar} usuarioId={usuarioIdPadrao} />);
    fireEvent.change(screen.getByPlaceholderText("Ex.: Maria da Silva, CPF ou P1001"), {
      target: { value: "P1001" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(await screen.findByText("Maria da Silva")).toBeInTheDocument();
    const chamada = fetchMock.mock.calls.find((chamada: unknown[]) =>
      String(chamada[0]).includes("/api/v1/legado/servidores"),
    );
    expect(String(chamada?.[0])).toContain("busca=P1001");
  });

  it("mostra estado vazio quando a busca não encontra ninguém", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta(200, [])));

    render(<Servidores permissoes={permissoesSemAlterar} usuarioId={usuarioIdPadrao} />);
    fireEvent.change(screen.getByPlaceholderText("Ex.: Maria da Silva, CPF ou P1001"), {
      target: { value: "Ninguém" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(
      await screen.findByText('Nenhum servidor encontrado para "Ninguém".'),
    ).toBeInTheDocument();
  });

  it("mostra mensagem de erro quando a API falha", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(403, { detail: "Sem permissão." })),
    );

    render(<Servidores permissoes={permissoesSemAlterar} usuarioId={usuarioIdPadrao} />);
    fireEvent.change(screen.getByPlaceholderText("Ex.: Maria da Silva, CPF ou P1001"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(await screen.findByText("Sem permissão.")).toBeInTheDocument();
  });

  it("abre o detalhe do servidor", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheSemHistoricoMedico));

    await abrirModal(fetchMock);

    expect(await screen.findByText("maria@example.test")).toBeInTheDocument();
    expect(screen.getAllByText("Em andamento").length).toBeGreaterThan(0);
  });

  it("oculta o histórico clínico quando o backend não o envia", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheSemHistoricoMedico));

    await abrirModal(fetchMock);

    await screen.findByText("maria@example.test");
    expect(screen.queryByText("Linha do tempo")).not.toBeInTheDocument();
    expect(screen.queryByText("Grupos de CID em atenção")).not.toBeInTheDocument();
    expect(screen.queryByText("Pareceres")).not.toBeInTheDocument();
  });

  it("mostra o histórico clínico quando o backend o autoriza", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico))
      .mockResolvedValueOnce(resposta(200, []));

    await abrirModal(fetchMock);

    expect(
      await screen.findByText(
        (_, elemento) =>
          elemento?.tagName === "H4" &&
          elemento?.textContent === "Z00.0 · Perícia médica de rotina",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Atestado · 15 dia(s)")).toBeInTheDocument();
    expect(screen.getByText("Atestado · 5 dia(s)")).toBeInTheDocument();
    expect(screen.getByText("Retorno em 30 dias.")).toBeInTheDocument();
    expect(screen.getAllByText("Atestado").length).toBe(2);
    expect(
      screen.getByText(
        (_, elemento) =>
          elemento?.className === "linha-do-tempo__tag" &&
          elemento?.textContent === "Consulta",
      ),
    ).toBeInTheDocument();

    expect(screen.getByText("Tramitação atual")).toBeInTheDocument();
    expect(screen.getAllByText("Em andamento").length).toBeGreaterThan(0);

    const cartaoAtestado = screen.getByText("dia(s) atestado").closest("span");
    expect(cartaoAtestado).toHaveTextContent("20");

    expect(screen.getByText("1 alerta(s)")).toBeInTheDocument();
    const alertaCid = screen.getByText("Grupos de CID em atenção").closest(".alerta-cid");
    expect(alertaCid).toHaveTextContent("Z00.0");
    expect(alertaCid).toHaveTextContent("20");

    fireEvent.click(screen.getByRole("button", { name: /Análise gráfica/ }));
    expect(screen.getByText("20d")).toBeInTheDocument();
  });

  it("mostra o histórico de pareceres sem formulário para quem só consulta", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico))
      .mockResolvedValueOnce(resposta(200, [parecerConcluido]));

    await abrirModal(fetchMock, permissoesSemAlterar);

    expect(await screen.findByText("Paciente apto, sem restrições.")).toBeInTheDocument();
    expect(screen.getByText("Apto para o trabalho")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Descreva a avaliação clínica/)).not.toBeInTheDocument();
  });

  it("mostra o formulário de parecer para quem pode alterar conteúdo médico", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico))
      .mockResolvedValueOnce(resposta(200, []));

    await abrirModal(fetchMock, permissoesComAlterar);

    expect(
      await screen.findByPlaceholderText(/Descreva a avaliação clínica/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Registrar e concluir" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salvar rascunho" })).toBeInTheDocument();
  });

  it("não mostra ação de editar em um parecer concluído", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico))
      .mockResolvedValueOnce(resposta(200, [parecerConcluido]));

    await abrirModal(fetchMock, permissoesComAlterar);

    await screen.findByText("Paciente apto, sem restrições.");
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
  });

  it("envia um novo parecer em rascunho", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico))
      .mockResolvedValueOnce(resposta(200, []))
      .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-teste" }))
      .mockResolvedValueOnce(resposta(201, parecerConcluido))
      .mockResolvedValueOnce(resposta(200, [parecerConcluido]));

    await abrirModal(fetchMock, permissoesComAlterar);

    const campoTexto = await screen.findByPlaceholderText(/Descreva a avaliação clínica/);
    fireEvent.change(campoTexto, {
      target: { value: "Paciente apto, sem restrições." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar rascunho" }));

    await screen.findByText("Paciente apto, sem restrições.");

    const chamadaDeCriacao = fetchMock.mock.calls.find(
      (chamada: unknown[]) => chamada[0] === "/api/v1/pareceres",
    );
    expect(chamadaDeCriacao).toBeDefined();
    const opcoesDaChamada = chamadaDeCriacao?.[1] as { body?: string } | undefined;
    const corpo = JSON.parse(opcoesDaChamada?.body ?? "{}");
    expect(corpo.servidor_sismed_id).toBe(1001);
    expect(corpo.concluir).toBe(false);
  });
});
