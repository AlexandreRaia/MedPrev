import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Servidores } from "./Servidores";

const servidorResumo = {
  id: 1001,
  nome: "Maria da Silva",
  nome_social: null,
  cpf: "123.456.789-00",
  email: "maria@example.test",
  ativo: true,
  admissao: "2020-01-01",
};

const servidorDetalheSemHistoricoMedico = {
  ...servidorResumo,
  nascimento: "1988-07-04",
  telefone: "1140000000",
  celular: "11999990000",
  protocolos: [{ id: 1, data: "2024-03-01", situacao: "Em andamento" }],
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
      data: "2024-03-05",
      motivo: "Perícia médica de rotina",
      subjetivo: "Paciente relata dor lombar recorrente.",
      objetivo: "Exame clínico sem alterações agudas.",
      conduta: "Encaminhado para acompanhamento.",
      relatorio: null,
      atestado: true,
      dias_atestado: 15,
    },
  ],
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

describe("Servidores", () => {
  it("pede um termo de busca antes de consultar a API", () => {
    vi.stubGlobal("fetch", vi.fn());

    render(<Servidores />);

    expect(
      screen.getByText("Digite um termo de busca para localizar um servidor."),
    ).toBeInTheDocument();
  });

  it("busca e lista os servidores encontrados", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, [servidorResumo])),
    );

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(await screen.findByText("Maria da Silva")).toBeInTheDocument();
    expect(
      screen.getByText(
        (_, elemento) => elemento?.textContent === "1 registro(s) encontrado(s)",
      ),
    ).toBeInTheDocument();
  });

  it("mostra estado vazio quando a busca não encontra ninguém", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta(200, [])));

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
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

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    expect(await screen.findByText("Sem permissão.")).toBeInTheDocument();
  });

  it("abre o detalhe do servidor com os protocolos", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheSemHistoricoMedico));
    vi.stubGlobal("fetch", fetchMock);

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Ver histórico →" }));

    expect(await screen.findByText("maria@example.test")).toBeInTheDocument();
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
  });

  it("oculta o histórico clínico quando o backend não o envia", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheSemHistoricoMedico));
    vi.stubGlobal("fetch", fetchMock);

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Ver histórico →" }));

    await screen.findByText("maria@example.test");
    expect(screen.queryByText("Histórico clínico")).not.toBeInTheDocument();
  });

  it("mostra o histórico clínico quando o backend o autoriza", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, [servidorResumo]))
      .mockResolvedValueOnce(resposta(200, servidorDetalheComHistoricoMedico));
    vi.stubGlobal("fetch", fetchMock);

    render(<Servidores />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 3 caracteres"), {
      target: { value: "Maria" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    fireEvent.click(await screen.findByRole("button", { name: "Ver histórico →" }));

    expect(await screen.findByText("Histórico clínico")).toBeInTheDocument();
    expect(screen.getByText("Perícia médica de rotina")).toBeInTheDocument();
    expect(screen.getByText("Atestado · 15 dia(s)")).toBeInTheDocument();
    expect(screen.getByText("Atestado")).toBeInTheDocument();
  });
});
