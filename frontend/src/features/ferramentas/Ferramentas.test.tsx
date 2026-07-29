import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Ferramentas } from "./Ferramentas";

afterEach(() => {
  cleanup();
});

describe("Ferramentas", () => {
  it("mostra os quatro cartões de ferramentas", () => {
    render(<Ferramentas />);

    expect(
      screen.getByRole("heading", { name: "Ferramentas" }),
    ).toBeInTheDocument();
    expect(screen.getByText("CID-10")).toBeInTheDocument();
    expect(screen.getByText("Calculadora de afastamento")).toBeInTheDocument();
    expect(screen.getByText("Modelos de parecer")).toBeInTheDocument();
    expect(screen.getByText("Relatórios")).toBeInTheDocument();
    expect(screen.getAllByText("Abrir ferramenta →")).toHaveLength(4);
  });
});
