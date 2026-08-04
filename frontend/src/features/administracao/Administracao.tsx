import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiError } from "../../shared/api/client";
import {
  alterarStatusUnidade,
  alterarStatus,
  configurarPermissoesPerfil,
  criarUnidade,
  criarUsuario,
  DadosUsuario,
  editarUnidade,
  editarUsuario,
  listarMatriz,
  listarUnidades,
  listarUsuarios,
  Perfil,
  redefinirSenha,
  Unidade,
  UsuarioAdministrativo,
} from "./api";

export type SecaoAdministrativa = "usuarios" | "unidades" | "matriz";

export function Administracao({
  secao,
  usuarioAtualId,
}: {
  secao: SecaoAdministrativa;
  usuarioAtualId: number;
}) {
  const [usuarios, setUsuarios] = useState<UsuarioAdministrativo[]>([]);
  const [unidades, setUnidades] = useState<Unidade[]>([]);
  const [matriz, setMatriz] = useState<Perfil[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const [novosUsuarios, novasUnidades, novaMatriz] = await Promise.all([
        listarUsuarios(),
        listarUnidades(),
        listarMatriz(),
      ]);
      setUsuarios(novosUsuarios);
      setUnidades(novasUnidades);
      setMatriz(novaMatriz);
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    let ativo = true;
    Promise.all([listarUsuarios(), listarUnidades(), listarMatriz()])
      .then(([novosUsuarios, novasUnidades, novaMatriz]) => {
        if (!ativo) return;
        setUsuarios(novosUsuarios);
        setUnidades(novasUnidades);
        setMatriz(novaMatriz);
      })
      .catch((error: unknown) => {
        if (ativo) setErro(mensagemDoErro(error));
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, []);

  if (carregando) {
    return <EstadoPainel texto="Carregando administração…" />;
  }

  if (erro) {
    return (
      <div className="estado-painel">
        <p role="alert">{erro}</p>
        <button className="botao botao--primario" onClick={() => void carregar()}>
          Tentar novamente
        </button>
      </div>
    );
  }

  if (secao === "unidades") {
    return (
      <TelaUnidades
        unidades={unidades}
        aoAtualizar={(unidade) =>
          setUnidades((atuais) => {
            const existe = atuais.some((item) => item.id === unidade.id);
            const resultado = existe
              ? atuais.map((item) => (item.id === unidade.id ? unidade : item))
              : [...atuais, unidade];
            return resultado.sort((a, b) => a.nome.localeCompare(b.nome));
          })
        }
      />
    );
  }

  if (secao === "matriz") {
    return (
      <TelaMatriz
        matriz={matriz}
        aoAtualizar={(perfilAtualizado) =>
          setMatriz((atual) =>
            atual.map((perfil) =>
              perfil.nome === perfilAtualizado.nome
                ? perfilAtualizado
                : perfil,
            ),
          )
        }
      />
    );
  }

  return (
    <TelaUsuarios
      usuarios={usuarios}
      unidades={unidades.filter((unidade) => unidade.ativa)}
      perfis={matriz.map((perfil) => perfil.nome)}
      usuarioAtualId={usuarioAtualId}
      aoAtualizar={(usuario) =>
        setUsuarios((atuais) => {
          const existe = atuais.some((item) => item.id === usuario.id);
          return existe
            ? atuais.map((item) => (item.id === usuario.id ? usuario : item))
            : [...atuais, usuario].sort((a, b) =>
                a.usuario.localeCompare(b.usuario),
              );
        })
      }
    />
  );
}

function CabecalhoSecao({
  legenda,
  titulo,
  descricao,
  acao,
}: {
  legenda: string;
  titulo: string;
  descricao: string;
  acao?: React.ReactNode;
}) {
  return (
    <header className="cabecalho-secao">
      <div>
        <p className="sobretitulo">{legenda}</p>
        <h1>{titulo}</h1>
        <p>{descricao}</p>
      </div>
      {acao}
    </header>
  );
}

function TelaUsuarios({
  usuarios,
  unidades,
  perfis,
  usuarioAtualId,
  aoAtualizar,
}: {
  usuarios: UsuarioAdministrativo[];
  unidades: Unidade[];
  perfis: string[];
  usuarioAtualId: number;
  aoAtualizar: (usuario: UsuarioAdministrativo) => void;
}) {
  const [busca, setBusca] = useState("");
  const [editando, setEditando] = useState<UsuarioAdministrativo | "novo" | null>(
    null,
  );
  const [redefinindo, setRedefinindo] =
    useState<UsuarioAdministrativo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [processandoId, setProcessandoId] = useState<number | null>(null);
  const usuariosFiltrados = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase();
    if (!termo) return usuarios;
    return usuarios.filter((usuario) =>
      [usuario.usuario, usuario.nome, usuario.email, usuario.unidade.nome]
        .join(" ")
        .toLocaleLowerCase()
        .includes(termo),
    );
  }, [busca, usuarios]);

  async function alternarStatus(usuario: UsuarioAdministrativo) {
    setProcessandoId(usuario.id);
    setErro(null);
    try {
      aoAtualizar(await alterarStatus(usuario.id, !usuario.ativo));
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setProcessandoId(null);
    }
  }

  return (
    <>
      <CabecalhoSecao
        legenda="Administração"
        titulo="Usuários e acessos"
        descricao="Cadastre pessoas, atribua um único perfil e defina a unidade responsável."
        acao={
          <button
            className="botao botao--primario"
            onClick={() => setEditando("novo")}
          >
            + Novo usuário
          </button>
        }
      />
      <section className="painel">
        <div className="barra-filtros">
          <label className="campo-busca">
            <span>Buscar usuário</span>
            <input
              value={busca}
              onChange={(event) => setBusca(event.target.value)}
              placeholder="Nome, acesso, e-mail ou unidade"
            />
          </label>
          <span className="contador-registros">
            {usuariosFiltrados.length} usuário(s)
          </span>
        </div>
        {erro ? (
          <p className="mensagem-erro" role="alert">
            {erro}
          </p>
        ) : null}
        <div className="tabela-responsiva">
          <table>
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Unidade</th>
                <th>Perfil</th>
                <th>Status</th>
                <th aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {usuariosFiltrados.map((usuario) => (
                <tr key={usuario.id}>
                  <td>
                    <div className="identidade-usuario">
                      <span aria-hidden="true">{iniciais(usuario.nome)}</span>
                      <div>
                        <strong>{usuario.nome}</strong>
                        <small>
                          {usuario.usuario}
                          {usuario.email ? ` · ${usuario.email}` : ""}
                        </small>
                      </div>
                    </div>
                  </td>
                  <td>{usuario.unidade.nome}</td>
                  <td>{usuario.perfil || "Sem perfil"}</td>
                  <td>
                    <span
                      className={`status status--${usuario.ativo ? "ativo" : "inativo"}`}
                    >
                      {usuario.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td>
                    <div className="acoes-tabela">
                      <button onClick={() => setEditando(usuario)}>Editar</button>
                      <button onClick={() => setRedefinindo(usuario)}>
                        Senha
                      </button>
                      <button
                        onClick={() => void alternarStatus(usuario)}
                        disabled={
                          processandoId === usuario.id ||
                          (usuario.id === usuarioAtualId && usuario.ativo)
                        }
                      >
                        {usuario.ativo ? "Desativar" : "Ativar"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {editando ? (
        <FormularioUsuario
          usuario={editando === "novo" ? null : editando}
          unidades={unidades}
          perfis={perfis}
          aoFechar={() => setEditando(null)}
          aoSalvar={(usuario) => {
            aoAtualizar(usuario);
            setEditando(null);
          }}
        />
      ) : null}
      {redefinindo ? (
        <FormularioSenha
          usuario={redefinindo}
          aoFechar={() => setRedefinindo(null)}
        />
      ) : null}
    </>
  );
}

function FormularioUsuario({
  usuario,
  unidades,
  perfis,
  aoFechar,
  aoSalvar,
}: {
  usuario: UsuarioAdministrativo | null;
  unidades: Unidade[];
  perfis: string[];
  aoFechar: () => void;
  aoSalvar: (usuario: UsuarioAdministrativo) => void;
}) {
  const [nome, setNome] = useState(usuario?.nome ?? "");
  const [acesso, setAcesso] = useState(usuario?.usuario ?? "");
  const [email, setEmail] = useState(usuario?.email ?? "");
  const [perfil, setPerfil] = useState(usuario?.perfil ?? perfis[0] ?? "");
  const [unidadeId, setUnidadeId] = useState(
    usuario?.unidade.id ?? unidades[0]?.id ?? 0,
  );
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function submeter(event: FormEvent) {
    event.preventDefault();
    setSalvando(true);
    setErro(null);
    const dados: DadosUsuario = {
      nome,
      email,
      perfil,
      unidade_id: unidadeId,
    };
    try {
      const resultado = usuario
        ? await editarUsuario(usuario.id, dados)
        : await criarUsuario({
            ...dados,
            usuario: acesso,
            senha_temporaria: senha,
          });
      aoSalvar(resultado);
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="modal-fundo" role="presentation">
      <section className="modal" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <div>
            <p className="sobretitulo">Controle de acesso</p>
            <h2>{usuario ? "Editar usuário" : "Novo usuário"}</h2>
          </div>
          <button className="fechar-modal" onClick={aoFechar} aria-label="Fechar">
            ×
          </button>
        </div>
        <form className="formulario-administrativo" onSubmit={submeter}>
          <label>
            Nome completo
            <input
              value={nome}
              onChange={(event) => setNome(event.target.value)}
              required
            />
          </label>
          <label>
            Usuário de acesso
            <input
              value={acesso}
              onChange={(event) => setAcesso(event.target.value)}
              disabled={Boolean(usuario)}
              required
            />
          </label>
          <label>
            E-mail
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          {!usuario ? (
            <label>
              Senha temporária
              <input
                type="password"
                value={senha}
                onChange={(event) => setSenha(event.target.value)}
                minLength={8}
                required
              />
            </label>
          ) : null}
          <label>
            Unidade
            <select
              value={unidadeId}
              onChange={(event) => setUnidadeId(Number(event.target.value))}
              required
            >
              {unidades.map((unidade) => (
                <option key={unidade.id} value={unidade.id}>
                  {unidade.nome}
                </option>
              ))}
            </select>
          </label>
          <label>
            Perfil
            <select
              value={perfil}
              onChange={(event) => setPerfil(event.target.value)}
              required
            >
              {perfis.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          {erro ? (
            <p className="mensagem-erro formulario-administrativo__erro">
              {erro}
            </p>
          ) : null}
          <div className="modal__acoes">
            <button
              type="button"
              className="botao botao--secundario"
              onClick={aoFechar}
            >
              Cancelar
            </button>
            <button className="botao botao--primario" disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar usuário"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function FormularioSenha({
  usuario,
  aoFechar,
}: {
  usuario: UsuarioAdministrativo;
  aoFechar: () => void;
}) {
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function submeter(event: FormEvent) {
    event.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      await redefinirSenha(usuario.id, senha);
      aoFechar();
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="modal-fundo">
      <section className="modal modal--compacto" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <div>
            <p className="sobretitulo">Credenciais</p>
            <h2>Redefinir senha</h2>
          </div>
          <button className="fechar-modal" onClick={aoFechar} aria-label="Fechar">
            ×
          </button>
        </div>
        <p>
          Defina uma senha temporária para <strong>{usuario.nome}</strong>.
        </p>
        <form className="formulario-administrativo" onSubmit={submeter}>
          <label>
            Nova senha temporária
            <input
              type="password"
              value={senha}
              onChange={(event) => setSenha(event.target.value)}
              minLength={8}
              required
              autoFocus
            />
          </label>
          {erro ? <p className="mensagem-erro">{erro}</p> : null}
          <div className="modal__acoes">
            <button
              type="button"
              className="botao botao--secundario"
              onClick={aoFechar}
            >
              Cancelar
            </button>
            <button className="botao botao--primario" disabled={salvando}>
              {salvando ? "Salvando…" : "Redefinir senha"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function TelaUnidades({
  unidades,
  aoAtualizar,
}: {
  unidades: Unidade[];
  aoAtualizar: (unidade: Unidade) => void;
}) {
  const [formulario, setFormulario] = useState<Unidade | "nova" | null>(null);
  const [busca, setBusca] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [processandoId, setProcessandoId] = useState<number | null>(null);
  const unidadesFiltradas = useMemo(() => {
    const termo = busca.trim().toLocaleLowerCase();
    if (!termo) return unidades;
    return unidades.filter((unidade) =>
      [unidade.nome, unidade.codigo, unidade.tipo_descricao]
        .join(" ")
        .toLocaleLowerCase()
        .includes(termo),
    );
  }, [busca, unidades]);

  async function alternarStatus(unidade: Unidade) {
    setProcessandoId(unidade.id);
    setErro(null);
    try {
      aoAtualizar(await alterarStatusUnidade(unidade.id, !unidade.ativa));
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setProcessandoId(null);
    }
  }

  return (
    <>
      <CabecalhoSecao
        legenda="Estrutura organizacional"
        titulo="Unidades"
        descricao="Cada usuário pertence a uma unidade, que será usada para limitar o acesso aos dados."
        acao={
          <button
            className="botao botao--primario"
            onClick={() => setFormulario("nova")}
          >
            + Nova unidade
          </button>
        }
      />
      <section className="painel">
        <div className="barra-filtros">
          <label className="campo-busca">
            <span>Buscar unidade</span>
            <input
              value={busca}
              onChange={(event) => setBusca(event.target.value)}
              placeholder="Nome, código ou tipo"
            />
          </label>
          <span className="contador-registros">
            {unidadesFiltradas.length} unidade(s)
          </span>
        </div>
        {erro ? (
          <p className="mensagem-erro mensagem-erro--tabela" role="alert">
            {erro}
          </p>
        ) : null}
        <div className="tabela-responsiva">
          <table>
            <thead>
              <tr>
                <th>Unidade</th>
                <th>Código</th>
                <th>Tipo</th>
                <th>Usuários</th>
                <th>Status</th>
                <th aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {unidadesFiltradas.map((unidade) => (
                <tr key={unidade.id}>
                  <td>
                    <strong>{unidade.nome}</strong>
                  </td>
                  <td>
                    <code>{unidade.codigo}</code>
                  </td>
                  <td>{unidade.tipo_descricao}</td>
                  <td>
                    <strong>{unidade.usuarios_ativos}</strong> ativo(s)
                    <small className="texto-secundario">
                      {unidade.usuarios_vinculados} vinculado(s)
                    </small>
                  </td>
                  <td>
                    <span
                      className={`status status--${unidade.ativa ? "ativo" : "inativo"}`}
                    >
                      {unidade.ativa ? "Ativa" : "Inativa"}
                    </span>
                  </td>
                  <td>
                    <div className="acoes-tabela">
                      <button onClick={() => setFormulario(unidade)}>
                        Editar
                      </button>
                      <button
                        onClick={() => void alternarStatus(unidade)}
                        disabled={processandoId === unidade.id}
                        title={
                          unidade.ativa && unidade.usuarios_ativos > 0
                            ? "Transfira ou desative os usuários ativos primeiro"
                            : undefined
                        }
                      >
                        {unidade.ativa ? "Desativar" : "Reativar"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {formulario ? (
        <FormularioUnidade
          unidade={formulario === "nova" ? null : formulario}
          aoFechar={() => setFormulario(null)}
          aoSalvar={(unidade) => {
            aoAtualizar(unidade);
            setFormulario(null);
          }}
        />
      ) : null}
    </>
  );
}

function FormularioUnidade({
  unidade,
  aoFechar,
  aoSalvar,
}: {
  unidade: Unidade | null;
  aoFechar: () => void;
  aoSalvar: (unidade: Unidade) => void;
}) {
  const [nome, setNome] = useState(unidade?.nome ?? "");
  const [codigo, setCodigo] = useState(unidade?.codigo ?? "");
  const [tipo, setTipo] = useState(unidade?.tipo ?? "secretaria");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function submeter(event: FormEvent) {
    event.preventDefault();
    setErro(null);
    setSalvando(true);
    try {
      const dados = { nome, codigo, tipo };
      aoSalvar(
        unidade
          ? await editarUnidade(unidade.id, dados)
          : await criarUnidade(dados),
      );
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="modal-fundo">
      <section className="modal modal--compacto" role="dialog" aria-modal="true">
        <div className="modal__cabecalho">
          <div>
            <p className="sobretitulo">Estrutura</p>
            <h2>{unidade ? "Editar unidade" : "Nova unidade"}</h2>
          </div>
          <button className="fechar-modal" onClick={aoFechar} aria-label="Fechar">
            ×
          </button>
        </div>
        <form className="formulario-administrativo" onSubmit={submeter}>
          <label>
            Nome
            <input
              value={nome}
              onChange={(event) => {
                const valor = event.target.value;
                setNome(valor);
                setCodigo(
                  valor
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "")
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, "-")
                    .replace(/(^-|-$)/g, ""),
                );
              }}
              required
            />
          </label>
          <label>
            Código
            <input
              value={codigo}
              onChange={(event) => setCodigo(event.target.value)}
              pattern="[a-z0-9-]+"
              required
            />
          </label>
          <label>
            Tipo
            <select value={tipo} onChange={(event) => setTipo(event.target.value)}>
              <option value="secretaria">Secretaria</option>
              <option value="administracao">Administração</option>
              <option value="medicina_trabalho">Medicina do Trabalho</option>
              <option value="caixa_previdencia">Caixa de Previdência</option>
            </select>
          </label>
          {erro ? <p className="mensagem-erro">{erro}</p> : null}
          <div className="modal__acoes">
            <button
              type="button"
              className="botao botao--secundario"
              onClick={aoFechar}
            >
              Cancelar
            </button>
            <button className="botao botao--primario" disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar unidade"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

const PERMISSOES_DISPONIVEIS = [
  "gerenciar_acessos",
  "consultar_dados",
  "alterar_dados_administrativos",
  "consultar_conteudo_medico",
  "alterar_conteudo_medico",
  "visualizar_dados_globais",
  "solicitar_apoio_especializado",
  "responder_solicitacao_apoio",
];

function TelaMatriz({
  matriz,
  aoAtualizar,
}: {
  matriz: Perfil[];
  aoAtualizar: (perfil: Perfil) => void;
}) {
  const [configuracao, setConfiguracao] = useState<Perfil[]>(() =>
    matriz.map((perfil) => ({
      ...perfil,
      permissoes: [...perfil.permissoes],
    })),
  );
  const [original, setOriginal] = useState(() =>
    matriz.map((perfil) => ({
      ...perfil,
      permissoes: [...perfil.permissoes],
    })),
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const alteracoesPendentes = configuracao.some((perfil, indice) => {
    const atuais = [...perfil.permissoes].sort().join(",");
    const anteriores = [...original[indice].permissoes].sort().join(",");
    return atuais !== anteriores;
  });

  function alternar(perfilNome: string, permissao: string) {
    if (perfilNome === "Administrador" && permissao === "gerenciar_acessos") {
      return;
    }
    setSucesso(null);
    setConfiguracao((atual) =>
      atual.map((perfil) => {
        if (perfil.nome !== perfilNome) return perfil;
        const possui = perfil.permissoes.includes(permissao);
        return {
          ...perfil,
          permissoes: possui
            ? perfil.permissoes.filter((item) => item !== permissao)
            : [...perfil.permissoes, permissao],
        };
      }),
    );
  }

  async function salvar() {
    setSalvando(true);
    setErro(null);
    setSucesso(null);
    try {
      const atualizados: Perfil[] = [];
      for (let indice = 0; indice < configuracao.length; indice += 1) {
        const perfil = configuracao[indice];
        const atual = [...perfil.permissoes].sort().join(",");
        const anterior = [...original[indice].permissoes].sort().join(",");
        if (atual !== anterior) {
          const atualizado = await configurarPermissoesPerfil(
            perfil.nome,
            perfil.permissoes,
          );
          atualizados.push(atualizado);
          aoAtualizar(atualizado);
        }
      }
      const novaBase = configuracao.map((perfil) => {
        const atualizado = atualizados.find(
          (item) => item.nome === perfil.nome,
        );
        return {
          ...(atualizado ?? perfil),
          permissoes: [...(atualizado ?? perfil).permissoes],
        };
      });
      setConfiguracao(novaBase);
      setOriginal(novaBase);
      setSucesso("Matriz de acesso atualizada com sucesso.");
    } catch (error) {
      setErro(mensagemDoErro(error));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <>
      <CabecalhoSecao
        legenda="Segurança"
        titulo="Matriz de acesso"
        descricao="Marque as ações permitidas para cada perfil. As alterações são verificadas e aplicadas pelo backend."
        acao={
          <div className="acoes-matriz">
            {alteracoesPendentes ? (
              <button
                className="botao botao--secundario"
                onClick={() =>
                  setConfiguracao(
                    original.map((perfil) => ({
                      ...perfil,
                      permissoes: [...perfil.permissoes],
                    })),
                  )
                }
                disabled={salvando}
              >
                Descartar
              </button>
            ) : null}
            <button
              className="botao botao--primario"
              onClick={() => void salvar()}
              disabled={!alteracoesPendentes || salvando}
            >
              {salvando ? "Salvando…" : "Salvar alterações"}
            </button>
          </div>
        }
      />
      {erro ? (
        <p className="mensagem-erro" role="alert">
          {erro}
        </p>
      ) : null}
      {sucesso ? (
        <p className="mensagem-sucesso" role="status">
          {sucesso}
        </p>
      ) : null}
      <section className="painel tabela-responsiva">
        <table className="matriz-acesso">
          <thead>
            <tr>
              <th>Permissão</th>
              {configuracao.map((perfil) => (
                <th key={perfil.nome}>{perfil.nome}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERMISSOES_DISPONIVEIS.map((permissao) => (
              <tr key={permissao}>
                <td>{formatarPermissao(permissao)}</td>
                {configuracao.map((perfil) => {
                  const marcada = perfil.permissoes.includes(permissao);
                  const protegida =
                    perfil.nome === "Administrador" &&
                    permissao === "gerenciar_acessos";
                  return (
                  <td key={perfil.nome}>
                    <label
                      className={`controle-permissao${marcada ? " controle-permissao--marcada" : ""}`}
                      title={
                        protegida
                          ? "O Administrador deve manter o gerenciamento de acessos"
                          : undefined
                      }
                    >
                      <input
                        type="checkbox"
                        checked={marcada}
                        onChange={() => alternar(perfil.nome, permissao)}
                        disabled={protegida || salvando}
                        aria-label={`${formatarPermissao(permissao)} — ${perfil.nome}`}
                      />
                      <span aria-hidden="true">{marcada ? "✓" : ""}</span>
                    </label>
                  </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function EstadoPainel({ texto }: { texto: string }) {
  return (
    <div className="estado-painel" aria-live="polite">
      <span className="carregando-indicador" aria-hidden="true" />
      <p>{texto}</p>
    </div>
  );
}

function mensagemDoErro(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a operação.";
}

function iniciais(nome: string): string {
  return nome
    .split(" ")
    .slice(0, 2)
    .map((parte) => parte.charAt(0))
    .join("")
    .toUpperCase();
}

function formatarPermissao(permissao: string): string {
  const texto = permissao.replaceAll("_", " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
