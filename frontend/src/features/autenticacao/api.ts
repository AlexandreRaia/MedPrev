import { apiGet, apiPost } from "../../shared/api/client";

export type UsuarioSessao = {
  id: number;
  usuario: string;
  nome: string;
  email: string;
  grupos: string[];
  permissoes: string[];
  superusuario: boolean;
  deve_trocar_senha: boolean;
  unidade: {
    id: number;
    codigo: string;
    nome: string;
  };
};

type CsrfResponse = {
  csrf_token: string;
};

type LogoutResponse = {
  mensagem: string;
};

export function consultarSessao(
  signal?: AbortSignal,
): Promise<UsuarioSessao> {
  return apiGet<UsuarioSessao>("/api/v1/auth/me", signal);
}

export async function obterCsrf(): Promise<string> {
  const response = await apiGet<CsrfResponse>("/api/v1/auth/csrf");
  return response.csrf_token;
}

export async function entrar(
  usuario: string,
  senha: string,
): Promise<UsuarioSessao> {
  const csrfToken = await obterCsrf();
  return apiPost<UsuarioSessao>(
    "/api/v1/auth/login",
    { usuario, senha },
    csrfToken,
  );
}

export async function sair(): Promise<void> {
  const csrfToken = await obterCsrf();
  await apiPost<LogoutResponse>("/api/v1/auth/logout", {}, csrfToken);
}

export async function alterarMinhaSenha(
  senhaAtual: string,
  novaSenha: string,
): Promise<void> {
  const csrfToken = await obterCsrf();
  await apiPost<LogoutResponse>(
    "/api/v1/auth/alterar-senha",
    { senha_atual: senhaAtual, nova_senha: novaSenha },
    csrfToken,
  );
}
