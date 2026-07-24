import { useEffect, useState } from "react";

import {
  Administracao,
  SecaoAdministrativa,
} from "../features/administracao/Administracao";
import {
  consultarSessao,
  sair,
  UsuarioSessao,
} from "../features/autenticacao/api";
import {
  Login,
  Marca,
  TrocaSenhaObrigatoria,
} from "../features/autenticacao/Login";
import { ApiError } from "../shared/api/client";

type EstadoSessao =
  | { tipo: "carregando" }
  | { tipo: "anonimo" }
  | { tipo: "autenticado"; usuario: UsuarioSessao }
  | { tipo: "erro" };

type Tela = "inicio" | SecaoAdministrativa;

export function App() {
  const [estado, setEstado] = useState<EstadoSessao>({ tipo: "carregando" });
  const [saindo, setSaindo] = useState(false);
  const [erroLogout, setErroLogout] = useState<string | null>(null);

  useEffect(() => {
    const controlador = new AbortController();
    resolverEstadoDaSessao(controlador.signal)
      .then(setEstado)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setEstado({ tipo: "erro" });
        }
      });
    return () => controlador.abort();
  }, []);

  function carregarSessao() {
    setEstado({ tipo: "carregando" });
    resolverEstadoDaSessao()
      .then(setEstado)
      .catch(() => setEstado({ tipo: "erro" }));
  }

  async function encerrarSessao() {
    setSaindo(true);
    setErroLogout(null);
    try {
      await sair();
      setEstado({ tipo: "anonimo" });
    } catch {
      setErroLogout("Não foi possível sair. Tente novamente.");
    } finally {
      setSaindo(false);
    }
  }

  if (estado.tipo === "carregando") return <TelaCarregamento />;
  if (estado.tipo === "erro") {
    return <TelaIndisponivel aoTentarNovamente={carregarSessao} />;
  }
  if (estado.tipo === "anonimo") {
    return (
      <Login
        aoAutenticar={(usuario) =>
          setEstado({ tipo: "autenticado", usuario })
        }
      />
    );
  }

  if (estado.usuario.deve_trocar_senha) {
    return (
      <TrocaSenhaObrigatoria
        usuario={estado.usuario}
        aoConcluir={() =>
          setEstado({
            tipo: "autenticado",
            usuario: { ...estado.usuario, deve_trocar_senha: false },
          })
        }
        aoSair={() => void encerrarSessao()}
      />
    );
  }

  return (
    <Aplicacao
      usuario={estado.usuario}
      saindo={saindo}
      erroLogout={erroLogout}
      aoSair={encerrarSessao}
    />
  );
}

async function resolverEstadoDaSessao(
  signal?: AbortSignal,
): Promise<EstadoSessao> {
  try {
    return { tipo: "autenticado", usuario: await consultarSessao(signal) };
  } catch (error: unknown) {
    if (error instanceof ApiError && error.statusCode === 401) {
      return { tipo: "anonimo" };
    }
    throw error;
  }
}

function Aplicacao({
  usuario,
  saindo,
  erroLogout,
  aoSair,
}: {
  usuario: UsuarioSessao;
  saindo: boolean;
  erroLogout: string | null;
  aoSair: () => void;
}) {
  const [tela, setTela] = useState<Tela>("inicio");
  const podeAdministrar = usuario.permissoes.includes("gerenciar_acessos");
  const perfil = usuario.grupos[0] ?? "Sem perfil atribuído";

  return (
    <div className="aplicacao">
      <header className="topbar">
        <Marca variante="clara" />
        <div className="topbar__titulo">
          <strong>Saúde ocupacional e previdenciária</strong>
          <span>Ambiente de desenvolvimento · Dados fictícios</span>
        </div>
        <div className="usuario-menu">
          <span className="avatar" aria-hidden="true">
            {usuario.nome.charAt(0).toUpperCase()}
          </span>
          <div>
            <strong>{usuario.nome}</strong>
            <span>{perfil}</span>
          </div>
          <button
            className="botao botao--topbar"
            type="button"
            onClick={aoSair}
            disabled={saindo}
          >
            {saindo ? "Saindo…" : "Sair"}
          </button>
        </div>
      </header>
      <div className="estrutura-app">
        <aside className="navegacao-lateral">
          <div className="navegacao-lateral__contexto">
            <span>Unidade atual</span>
            <strong>{usuario.unidade.nome}</strong>
          </div>
          <nav aria-label="Navegação principal">
            <BotaoNavegacao
              ativo={tela === "inicio"}
              icone="⌂"
              texto="Visão geral"
              aoClicar={() => setTela("inicio")}
            />
            <BotaoNavegacao
              ativo={false}
              icone="♙"
              texto="Servidores"
              desabilitado
            />
            <BotaoNavegacao
              ativo={false}
              icone="▤"
              texto="Atendimentos"
              desabilitado
            />
            <BotaoNavegacao
              ativo={false}
              icone="◫"
              texto="Relatórios"
              desabilitado
            />
            {podeAdministrar ? (
              <>
                <p className="navegacao-lateral__grupo">Administração</p>
                <BotaoNavegacao
                  ativo={tela === "usuarios"}
                  icone="◎"
                  texto="Usuários"
                  aoClicar={() => setTela("usuarios")}
                />
                <BotaoNavegacao
                  ativo={tela === "unidades"}
                  icone="▦"
                  texto="Unidades"
                  aoClicar={() => setTela("unidades")}
                />
                <BotaoNavegacao
                  ativo={tela === "matriz"}
                  icone="✓"
                  texto="Matriz de acesso"
                  aoClicar={() => setTela("matriz")}
                />
              </>
            ) : null}
          </nav>
          <div className="navegacao-lateral__rodape">
            <span className="sessao-ativa">
              <span aria-hidden="true" />
              Sessão segura
            </span>
          </div>
        </aside>
        <main className="conteudo-app">
          {erroLogout ? (
            <p className="mensagem-erro mensagem-erro--pagina" role="alert">
              {erroLogout}
            </p>
          ) : null}
          {tela === "inicio" ? (
            <PainelInicial usuario={usuario} perfil={perfil} />
          ) : podeAdministrar ? (
            <Administracao
              secao={tela}
              usuarioAtualId={usuario.id}
            />
          ) : null}
        </main>
      </div>
    </div>
  );
}

function BotaoNavegacao({
  ativo,
  icone,
  texto,
  aoClicar,
  desabilitado = false,
}: {
  ativo: boolean;
  icone: string;
  texto: string;
  aoClicar?: () => void;
  desabilitado?: boolean;
}) {
  return (
    <button
      className={`item-navegacao${ativo ? " item-navegacao--ativo" : ""}`}
      type="button"
      onClick={aoClicar}
      disabled={desabilitado}
      title={desabilitado ? "Disponível em uma próxima etapa" : undefined}
    >
      <span aria-hidden="true">{icone}</span>
      {texto}
      {desabilitado ? <small>Em breve</small> : null}
    </button>
  );
}

function PainelInicial({
  usuario,
  perfil,
}: {
  usuario: UsuarioSessao;
  perfil: string;
}) {
  return (
    <>
      <header className="cabecalho-secao">
        <div>
          <p className="sobretitulo">Painel principal</p>
          <h1>Olá, {usuario.nome}</h1>
          <p>
            Esta é a visão inicial da sua unidade. Os próximos indicadores serão
            conectados aos fluxos do MVP.
          </p>
        </div>
        <span className="data-atual">
          Unidade: <strong>{usuario.unidade.nome}</strong>
        </span>
      </header>
      <section className="grade-indicadores" aria-label="Resumo do acesso">
        <CartaoIndicador
          tom="azul"
          icone="◎"
          valor={perfil}
          rotulo="Perfil de acesso"
          detalhe="Autorizações validadas pela API"
        />
        <CartaoIndicador
          tom="verde"
          icone="✓"
          valor={String(usuario.permissoes.length)}
          rotulo="Permissões ativas"
          detalhe="Aplicadas nesta sessão"
        />
        <CartaoIndicador
          tom="amarelo"
          icone="◷"
          valor="0"
          rotulo="Pendências"
          detalhe="Módulo operacional em preparação"
        />
        <CartaoIndicador
          tom="roxo"
          icone="▦"
          valor={usuario.unidade.nome}
          rotulo="Escopo de dados"
          detalhe={
            usuario.permissoes.includes("visualizar_dados_globais")
              ? "Visão global autorizada"
              : "Restrito à unidade vinculada"
          }
        />
      </section>
      <section className="painel painel--boas-vindas">
        <div>
          <p className="sobretitulo">Próxima etapa</p>
          <h2>Cadastro e consulta de servidores</h2>
          <p>
            A fundação de autenticação, unidades e controle de acesso está
            pronta para receber o primeiro fluxo operacional.
          </p>
        </div>
        <div className="painel--boas-vindas__selo" aria-hidden="true">
          MVP
        </div>
      </section>
    </>
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

function TelaCarregamento() {
  return (
    <main className="tela-estado" aria-live="polite">
      <Marca />
      <span className="carregando-indicador" aria-hidden="true" />
      <p>Verificando sua sessão…</p>
    </main>
  );
}

function TelaIndisponivel({
  aoTentarNovamente,
}: {
  aoTentarNovamente: () => void;
}) {
  return (
    <main className="tela-estado">
      <Marca />
      <div className="estado-icone" aria-hidden="true">
        !
      </div>
      <h1>Não foi possível acessar o MedPrev</h1>
      <p>Confirme se o servidor está ativo e tente novamente.</p>
      <button
        className="botao botao--primario"
        type="button"
        onClick={aoTentarNovamente}
      >
        Tentar novamente
      </button>
    </main>
  );
}
