import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("App", () => {
  it("mostra que a API está disponível", async () => {
    const resposta = {
      ok: true,
      status: 200,
      json: async () => ({
        status: "ok",
        service: "medprev-api",
      }),
    } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta));

    render(<App />);

    expect(screen.getByText("Verificando a API…")).toBeInTheDocument();
    expect(await screen.findByText("API disponível")).toBeInTheDocument();
    expect(screen.getByText("medprev-api")).toBeInTheDocument();
  });

  it("orienta quando a API está indisponível", async () => {
    const resposta = {
      ok: false,
      status: 503,
    } as Response;
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(resposta));

    render(<App />);

    expect(
      await screen.findByText(
        "API indisponível. Confirme se o backend está em execução.",
      ),
    ).toBeInTheDocument();
  });
});
