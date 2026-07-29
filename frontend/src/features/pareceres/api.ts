import { apiGet, apiPatch, apiPost } from "../../shared/api/client";
import { obterCsrf } from "../autenticacao/api";

export type Parecer = {
  id: number;
  servidor_sismed_id: number;
  protocolo_sismed_id: number | null;
  autor: string;
  autor_id: number;
  unidade: string;
  texto: string;
  conclusao: string;
  conclusao_descricao: string;
  estado: string;
  estado_descricao: string;
  prioritario: boolean;
  data_reavaliacao: string | null;
  criado_em: string;
  atualizado_em: string;
  concluido_em: string | null;
};

export type DadosParecer = {
  texto: string;
  conclusao: string;
  prioritario: boolean;
  data_reavaliacao: string | null;
};

export function listarPareceres(servidorSismedId: number): Promise<Parecer[]> {
  const parametros = new URLSearchParams({
    servidor_sismed_id: String(servidorSismedId),
  });
  return apiGet(`/api/v1/pareceres?${parametros}`);
}

export async function criarParecer(
  servidorSismedId: number,
  dados: DadosParecer,
  concluir: boolean,
): Promise<Parecer> {
  return apiPost(
    "/api/v1/pareceres",
    { ...dados, servidor_sismed_id: servidorSismedId, concluir },
    await obterCsrf(),
  );
}

export async function editarParecer(
  parecerId: number,
  dados: DadosParecer,
): Promise<Parecer> {
  return apiPatch(`/api/v1/pareceres/${parecerId}`, dados, await obterCsrf());
}

export async function concluirParecer(parecerId: number): Promise<Parecer> {
  return apiPost(`/api/v1/pareceres/${parecerId}/concluir`, {}, await obterCsrf());
}
