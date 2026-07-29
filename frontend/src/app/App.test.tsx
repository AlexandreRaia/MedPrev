import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const usuarioAdministrador = {
  id: 1,
  usuario: "admin.medprev",
  nome: "Administrador MedPrev",
  email: "admin@medprev.local",
  grupos: ["Administrador"],
  permissoes: [
    "gerenciar_acessos",
    "consultar_dados",
    "alterar_dados_administrativos",
  ],
  superusuario: true,
  deve_trocar_senha: false,
  unidade: {
    id: 1,
    codigo: "administracao",
    nome: "Administração",
  },
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

describe("App", () => {
  it("mostra o login quando não existe sessão", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(401, { detail: "Unauthorized" })),
    );

    render(<App />);

    expect(screen.getByText("Verificando sua sessão…")).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Acesse sua conta" }),
    ).toBeInTheDocument();
  });

  it("pula o login quando a sessão já está ativa", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, usuarioAdministrador)),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Olá, Administrador MedPrev",
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Administrador").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Administração").length).toBeGreaterThan(0);
  });

  it("autentica e abre a tela principal", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(401, { detail: "Unauthorized" }))
      .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-teste" }))
      .mockResolvedValueOnce(resposta(200, usuarioAdministrador));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.change(await screen.findByLabelText("Usuário"), {
      target: { value: "admin.medprev" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), {
      target: { value: "MedPrev2026!" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(
      await screen.findByRole("heading", {
        name: "Olá, Administrador MedPrev",
      }),
    ).toBeInTheDocument();

    const loginRequest = fetchMock.mock.calls[2];
    expect(loginRequest[0]).toBe("/api/v1/auth/login");
    expect(loginRequest[1]).toMatchObject({
      method: "POST",
      credentials: "include",
      headers: expect.objectContaining({
        "X-CSRFToken": "csrf-teste",
      }),
    });
  });

  it("informa quando as credenciais são inválidas", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(resposta(401, { detail: "Unauthorized" }))
        .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-teste" }))
        .mockResolvedValueOnce(
          resposta(401, { detail: "Usuário ou senha inválidos." }),
        ),
    );

    render(<App />);

    fireEvent.change(await screen.findByLabelText("Usuário"), {
      target: { value: "incorreto" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), {
      target: { value: "incorreta" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(
      await screen.findByText("Usuário ou senha inválidos."),
    ).toBeInTheDocument();
  });

  it("encerra a sessão e volta ao login", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, usuarioAdministrador))
      .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-renovado" }))
      .mockResolvedValueOnce(resposta(200, { mensagem: "Sessão encerrada." }));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Sair" }));

    expect(
      await screen.findByRole("heading", { name: "Acesse sua conta" }),
    ).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("permite tentar novamente quando o backend está indisponível", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(503, { detail: "Indisponível" })),
    );

    render(<App />);

    expect(
      await screen.findByRole("heading", {
        name: "Não foi possível acessar o MedPrev",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Tentar novamente" }),
    ).toBeInTheDocument();
  });

  it("abre a gestão de usuários para quem possui permissão", async () => {
    const unidade = {
      id: 1,
      codigo: "administracao",
      nome: "Administração",
      tipo: "administracao",
      tipo_descricao: "Administração",
      ativa: true,
      usuarios_vinculados: 1,
      usuarios_ativos: 1,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, usuarioAdministrador))
      .mockResolvedValueOnce(
        resposta(200, [
          {
            id: 1,
            usuario: "admin.medprev",
            nome: "Administrador MedPrev",
            email: "admin@medprev.local",
            ativo: true,
            perfil: "Administrador",
            unidade,
            deve_trocar_senha: false,
          },
        ]),
      )
      .mockResolvedValueOnce(resposta(200, [unidade]))
      .mockResolvedValueOnce(
        resposta(200, [
          {
            nome: "Administrador",
            permissoes: ["gerenciar_acessos"],
          },
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Usuários" }));

    expect(
      await screen.findByRole("heading", { name: "Usuários e acessos" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/admin\.medprev/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Unidades" }));
    expect(
      screen.getByRole("heading", { name: "Unidades" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Código" })).toBeInTheDocument();
    expect(screen.getByText("administracao")).toBeInTheDocument();
  });

  it("mostra o painel de indicadores para quem tem a permissão", async () => {
    const usuarioGestor = {
      ...usuarioAdministrador,
      nome: "Gestora MedPrev",
      grupos: ["Gestor da Administração"],
      permissoes: [
        ...usuarioAdministrador.permissoes,
        "visualizar_indicadores_gerenciais",
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, usuarioGestor))
      .mockResolvedValueOnce(
        resposta(200, {
          servidores_acompanhados: 4,
          pericias_60_dias: 13,
          pareceres_em_rascunho: 2,
          pericias_com_atestado_60_dias: 5,
          grupos_cid: [{ codigo: "Z00.0", ocorrencias: 10 }],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Visão geral" })).toBeInTheDocument();
    expect(
      await screen.findByText("2 parecer(es) em rascunho aguardando conclusão."),
    ).toBeInTheDocument();
  });

  it("abre a página de ferramentas pelo menu lateral", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(resposta(200, usuarioAdministrador)),
    );

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Ferramentas" }));

    expect(
      await screen.findByRole("heading", { name: "Ferramentas" }),
    ).toBeInTheDocument();
    expect(screen.getByText("CID-10")).toBeInTheDocument();
  });

  it("permite configurar e salvar a matriz de acesso", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(resposta(200, usuarioAdministrador))
      .mockResolvedValueOnce(resposta(200, []))
      .mockResolvedValueOnce(resposta(200, []))
      .mockResolvedValueOnce(
        resposta(200, [
          {
            nome: "Administrador",
            permissoes: ["gerenciar_acessos"],
          },
          {
            nome: "Auditor",
            permissoes: ["consultar_dados", "visualizar_auditoria"],
          },
        ]),
      )
      .mockResolvedValueOnce(resposta(200, { csrf_token: "csrf-matriz" }))
      .mockResolvedValueOnce(
        resposta(200, {
          nome: "Auditor",
          permissoes: [
            "consultar_dados",
            "visualizar_auditoria",
            "visualizar_indicadores_gerenciais",
          ],
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Matriz de acesso" }),
    );
    const permissao = await screen.findByRole("checkbox", {
      name: "Visualizar indicadores gerenciais — Auditor",
    });
    fireEvent.click(permissao);
    fireEvent.click(
      screen.getByRole("button", { name: "Salvar alterações" }),
    );

    expect(
      await screen.findByText("Matriz de acesso atualizada com sucesso."),
    ).toBeInTheDocument();
    expect(fetchMock.mock.calls[5][0]).toBe(
      "/api/v1/administracao/perfis/Auditor/permissoes",
    );
    expect(fetchMock.mock.calls[5][1]).toMatchObject({
      method: "PATCH",
      headers: expect.objectContaining({
        "X-CSRFToken": "csrf-matriz",
      }),
    });
  });
});
