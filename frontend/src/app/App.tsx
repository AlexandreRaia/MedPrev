import { useEffect, useState } from "react";

import { consultarSaudeDaApi } from "../features/saude/api";

type EstadoDaApi =
  | { tipo: "carregando" }
  | { tipo: "disponivel"; servico: string }
  | { tipo: "indisponivel" };

export function App() {
  const [estadoDaApi, setEstadoDaApi] = useState<EstadoDaApi>({
    tipo: "carregando",
  });

  useEffect(() => {
    const controlador = new AbortController();

    consultarSaudeDaApi(controlador.signal)
      .then((resposta) => {
        setEstadoDaApi({
          tipo: "disponivel",
          servico: resposta.service,
        });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setEstadoDaApi({ tipo: "indisponivel" });
      });

    return () => controlador.abort();
  }, []);

  return (
    <div className="pagina">
      <header className="cabecalho">
        <a className="marca" href="/" aria-label="Página inicial do MedPrev">
          <span className="marca__simbolo" aria-hidden="true">
            M
          </span>
          <span>MedPrev</span>
        </a>
        <span className="ambiente">Estrutura inicial</span>
      </header>

      <main className="conteudo">
        <section className="apresentacao" aria-labelledby="titulo-principal">
          <p className="sobretitulo">Medicina preventiva</p>
          <h1 id="titulo-principal">Base técnica pronta para evoluir</h1>
          <p className="resumo">
            Django, Django Ninja, React e PostgreSQL organizados para receber as
            primeiras funcionalidades aprovadas do MedPrev.
          </p>
        </section>

        <section className="cartao" aria-labelledby="titulo-status">
          <div>
            <p className="cartao__rotulo">Conectividade</p>
            <h2 id="titulo-status">Status da API</h2>
          </div>
          <ApiStatus estado={estadoDaApi} />
        </section>

        <section className="proximos-passos" aria-labelledby="titulo-proximos">
          <h2 id="titulo-proximos">Próxima decisão</h2>
          <p>
            Definir o MVP, a matriz de permissões e a primeira consulta
            prioritária ao SisMed antes de criar regras de negócio.
          </p>
        </section>
      </main>
    </div>
  );
}

function ApiStatus({ estado }: { estado: EstadoDaApi }) {
  if (estado.tipo === "carregando") {
    return (
      <p className="status status--carregando" role="status">
        Verificando a API…
      </p>
    );
  }

  if (estado.tipo === "indisponivel") {
    return (
      <p className="status status--erro" role="alert">
        API indisponível. Confirme se o backend está em execução.
      </p>
    );
  }

  return (
    <p className="status status--sucesso" role="status">
      <span className="status__indicador" aria-hidden="true" />
      API disponível
      <span className="status__detalhe">{estado.servico}</span>
    </p>
  );
}
