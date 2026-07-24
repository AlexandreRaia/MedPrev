import { FormEvent, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { alterarMinhaSenha, entrar, UsuarioSessao } from "./api";

type LoginProps = {
  aoAutenticar: (usuario: UsuarioSessao) => void;
};

export function Login({ aoAutenticar }: LoginProps) {
  const [usuario, setUsuario] = useState("");
  const [senha, setSenha] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function submeter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEnviando(true);
    setErro(null);

    try {
      const sessao = await entrar(usuario.trim(), senha);
      aoAutenticar(sessao);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.statusCode === 401) {
        setErro("Usuário ou senha inválidos.");
      } else {
        setErro(
          "Não foi possível acessar o sistema. Verifique a conexão e tente novamente.",
        );
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="pagina-login">
      <section className="login-contexto" aria-label="Apresentação do MedPrev">
        <Marca variante="clara" />
        <div className="login-contexto__conteudo">
          <p className="sobretitulo sobretitulo--claro">
            Medicina preventiva
          </p>
          <h1>Cuidado organizado começa com informação segura.</h1>
          <p>
            Acesse o ambiente de trabalho do MedPrev para consultar e conduzir
            os fluxos autorizados para o seu perfil.
          </p>
        </div>
        <p className="login-contexto__rodape">
          Ambiente de desenvolvimento · Dados fictícios
        </p>
      </section>

      <section className="login-acesso" aria-labelledby="titulo-login">
        <div className="login-acesso__conteudo">
          <div className="login-acesso__marca">
            <Marca />
          </div>
          <p className="sobretitulo">Acesso restrito</p>
          <h2 id="titulo-login">Acesse sua conta</h2>
          <p className="login-acesso__instrucao">
            Informe as credenciais cadastradas pelo administrador.
          </p>

          <form className="formulario-login" onSubmit={submeter}>
            <label htmlFor="usuario">Usuário</label>
            <input
              id="usuario"
              name="usuario"
              type="text"
              value={usuario}
              onChange={(event) => setUsuario(event.target.value)}
              autoComplete="username"
              autoFocus
              required
              disabled={enviando}
            />

            <label htmlFor="senha">Senha</label>
            <input
              id="senha"
              name="senha"
              type="password"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
              autoComplete="current-password"
              required
              disabled={enviando}
            />

            {erro ? (
              <p className="mensagem-erro" role="alert">
                {erro}
              </p>
            ) : null}

            <button className="botao botao--primario" disabled={enviando}>
              {enviando ? "Entrando…" : "Entrar"}
            </button>
          </form>

          <p className="login-acesso__ajuda">
            Problemas de acesso? Procure o administrador do sistema.
          </p>
        </div>
      </section>
    </main>
  );
}

export function TrocaSenhaObrigatoria({
  usuario,
  aoConcluir,
  aoSair,
}: {
  usuario: UsuarioSessao;
  aoConcluir: () => void;
  aoSair: () => void;
}) {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function submeter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (novaSenha !== confirmacao) {
      setErro("A confirmação da nova senha não confere.");
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      await alterarMinhaSenha(senhaAtual, novaSenha);
      aoConcluir();
    } catch (error) {
      setErro(
        error instanceof ApiError
          ? error.message
          : "Não foi possível alterar a senha.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="tela-troca-senha">
      <section className="troca-senha-cartao">
        <Marca />
        <p className="sobretitulo">Primeiro acesso</p>
        <h1>Crie uma senha pessoal</h1>
        <p>
          Olá, {usuario.nome}. Por segurança, substitua a senha temporária antes
          de acessar o sistema.
        </p>
        <form className="formulario-login" onSubmit={submeter}>
          <label htmlFor="senha-atual">Senha temporária</label>
          <input
            id="senha-atual"
            type="password"
            value={senhaAtual}
            onChange={(event) => setSenhaAtual(event.target.value)}
            required
          />
          <label htmlFor="nova-senha">Nova senha</label>
          <input
            id="nova-senha"
            type="password"
            value={novaSenha}
            onChange={(event) => setNovaSenha(event.target.value)}
            minLength={8}
            required
          />
          <label htmlFor="confirmar-senha">Confirmar nova senha</label>
          <input
            id="confirmar-senha"
            type="password"
            value={confirmacao}
            onChange={(event) => setConfirmacao(event.target.value)}
            minLength={8}
            required
          />
          {erro ? (
            <p className="mensagem-erro" role="alert">
              {erro}
            </p>
          ) : null}
          <button className="botao botao--primario" disabled={enviando}>
            {enviando ? "Alterando…" : "Salvar nova senha"}
          </button>
          <button
            type="button"
            className="botao botao--secundario"
            onClick={aoSair}
          >
            Sair
          </button>
        </form>
      </section>
    </main>
  );
}

type MarcaProps = {
  variante?: "padrao" | "clara";
};

export function Marca({ variante = "padrao" }: MarcaProps) {
  return (
    <a
      className={`marca marca--${variante}`}
      href="/"
      aria-label="Página inicial do MedPrev"
    >
      <span className="marca__simbolo" aria-hidden="true">
        M
      </span>
      <span>MedPrev</span>
    </a>
  );
}
