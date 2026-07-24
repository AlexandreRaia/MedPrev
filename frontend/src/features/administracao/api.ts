import {
  apiGet,
  apiPatch,
  apiPost,
} from "../../shared/api/client";
import { obterCsrf } from "../autenticacao/api";

export type Unidade = {
  id: number;
  codigo: string;
  nome: string;
  tipo: string;
  tipo_descricao: string;
  ativa: boolean;
  usuarios_vinculados: number;
  usuarios_ativos: number;
};

export type UsuarioAdministrativo = {
  id: number;
  usuario: string;
  nome: string;
  email: string;
  ativo: boolean;
  perfil: string;
  unidade: Unidade;
  deve_trocar_senha: boolean;
};

export type Perfil = {
  nome: string;
  permissoes: string[];
};

export type DadosUsuario = {
  nome: string;
  email: string;
  perfil: string;
  unidade_id: number;
};

export function listarUsuarios(): Promise<UsuarioAdministrativo[]> {
  return apiGet("/api/v1/administracao/usuarios");
}

export function listarUnidades(): Promise<Unidade[]> {
  return apiGet("/api/v1/administracao/unidades");
}

export function listarMatriz(): Promise<Perfil[]> {
  return apiGet("/api/v1/auth/matriz");
}

export async function criarUsuario(
  dados: DadosUsuario & { usuario: string; senha_temporaria: string },
): Promise<UsuarioAdministrativo> {
  return apiPost(
    "/api/v1/administracao/usuarios",
    dados,
    await obterCsrf(),
  );
}

export async function editarUsuario(
  usuarioId: number,
  dados: DadosUsuario,
): Promise<UsuarioAdministrativo> {
  return apiPatch(
    `/api/v1/administracao/usuarios/${usuarioId}`,
    dados,
    await obterCsrf(),
  );
}

export async function alterarStatus(
  usuarioId: number,
  ativo: boolean,
): Promise<UsuarioAdministrativo> {
  const acao = ativo ? "ativar" : "desativar";
  return apiPost(
    `/api/v1/administracao/usuarios/${usuarioId}/${acao}`,
    {},
    await obterCsrf(),
  );
}

export async function redefinirSenha(
  usuarioId: number,
  senhaTemporaria: string,
): Promise<void> {
  await apiPost(
    `/api/v1/administracao/usuarios/${usuarioId}/redefinir-senha`,
    { senha_temporaria: senhaTemporaria },
    await obterCsrf(),
  );
}

export async function criarUnidade(dados: {
  codigo: string;
  nome: string;
  tipo: string;
}): Promise<Unidade> {
  return apiPost(
    "/api/v1/administracao/unidades",
    dados,
    await obterCsrf(),
  );
}

export async function editarUnidade(
  unidadeId: number,
  dados: { codigo: string; nome: string; tipo: string },
): Promise<Unidade> {
  return apiPatch(
    `/api/v1/administracao/unidades/${unidadeId}`,
    dados,
    await obterCsrf(),
  );
}

export async function alterarStatusUnidade(
  unidadeId: number,
  ativa: boolean,
): Promise<Unidade> {
  return apiPost(
    `/api/v1/administracao/unidades/${unidadeId}/${ativa ? "ativar" : "desativar"}`,
    {},
    await obterCsrf(),
  );
}

export async function configurarPermissoesPerfil(
  perfilNome: string,
  permissoes: string[],
): Promise<Perfil> {
  return apiPatch(
    `/api/v1/administracao/perfis/${encodeURIComponent(perfilNome)}/permissoes`,
    { permissoes },
    await obterCsrf(),
  );
}
