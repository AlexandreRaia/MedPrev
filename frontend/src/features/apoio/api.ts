import { apiGet, apiPost } from "../../shared/api/client";
import { obterCsrf } from "../autenticacao/api";

export type Especialidade =
  | "neuropsicologia"
  | "assistencia_social"
  | "seguranca_trabalho";

export type SolicitacaoApoio = {
  id: number;
  servidor_sismed_id: number;
  protocolo_sismed_id: number | null;
  especialidade: Especialidade;
  especialidade_descricao: string;
  solicitante: string;
  solicitante_id: number;
  unidade: string;
  texto_solicitacao: string;
  estado: "aberta" | "respondida";
  estado_descricao: string;
  respondente: string | null;
  texto_resposta: string;
  criado_em: string;
  respondido_em: string | null;
};

export type MinhaSolicitacaoApoio = SolicitacaoApoio & {
  servidor_nome: string | null;
};

export type ApoioPorEspecialidade = {
  especialidade: Especialidade;
  especialidade_descricao: string;
  estado: "aberta" | "respondida";
  estado_descricao: string;
};

export type AtendimentoAberto = {
  servidor_sismed_id: number;
  servidor_nome: string | null;
  situacao_protocolo: string | null;
  parecer_em_aberto: boolean;
  parecer_autor: string | null;
  apoios: ApoioPorEspecialidade[];
  ultima_atividade_em: string;
};

export type DadosSolicitacaoApoio = {
  servidor_sismed_id: number;
  protocolo_sismed_id?: number | null;
  especialidade: Especialidade;
  texto_solicitacao: string;
};

export function listarSolicitacoesDoServidor(
  servidorSismedId: number,
): Promise<SolicitacaoApoio[]> {
  const parametros = new URLSearchParams({
    servidor_sismed_id: String(servidorSismedId),
  });
  return apiGet(`/api/v1/apoio?${parametros}`);
}

export function listarMinhasSolicitacoes(
  signal?: AbortSignal,
): Promise<MinhaSolicitacaoApoio[]> {
  return apiGet("/api/v1/apoio/minhas", signal);
}

export function listarAtendimentos(
  signal?: AbortSignal,
): Promise<AtendimentoAberto[]> {
  return apiGet("/api/v1/apoio/atendimentos", signal);
}

export async function criarSolicitacao(
  dados: DadosSolicitacaoApoio,
): Promise<SolicitacaoApoio> {
  return apiPost("/api/v1/apoio", dados, await obterCsrf());
}

export async function responderSolicitacao(
  solicitacaoId: number,
  textoResposta: string,
): Promise<SolicitacaoApoio> {
  return apiPost(
    `/api/v1/apoio/${solicitacaoId}/responder`,
    { texto_resposta: textoResposta },
    await obterCsrf(),
  );
}
