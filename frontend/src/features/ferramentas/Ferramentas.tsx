const FERRAMENTAS = [
  {
    icone: "⌕",
    titulo: "CID-10",
    descricao: "Consulta rápida à classificação e grupos relacionados.",
  },
  {
    icone: "Σ",
    titulo: "Calculadora de afastamento",
    descricao: "Some períodos e identifique sobreposições.",
  },
  {
    icone: "≡",
    titulo: "Modelos de parecer",
    descricao: "Use textos padronizados pela gestão clínica.",
  },
  {
    icone: "↗",
    titulo: "Relatórios",
    descricao: "Exporte indicadores consolidados por período.",
  },
] as const;

export function Ferramentas() {
  return (
    <>
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Painel de atendimento</p>
          <h1>Ferramentas</h1>
          <p>Recursos de apoio ao fluxo clínico.</p>
        </div>
        <span className="data-atual">● Dados atualizados agora</span>
      </header>

      <section className="grade-ferramentas" aria-label="Ferramentas disponíveis">
        {FERRAMENTAS.map((ferramenta) => (
          <CartaoFerramenta key={ferramenta.titulo} {...ferramenta} />
        ))}
      </section>
    </>
  );
}

function CartaoFerramenta({
  icone,
  titulo,
  descricao,
}: {
  icone: string;
  titulo: string;
  descricao: string;
}) {
  return (
    <article className="cartao-ferramenta">
      <span className="cartao-ferramenta__icone" aria-hidden="true">
        {icone}
      </span>
      <h2>{titulo}</h2>
      <p>{descricao}</p>
      <span className="cartao-ferramenta__link">Abrir ferramenta →</span>
    </article>
  );
}
