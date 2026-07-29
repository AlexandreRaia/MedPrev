import { apiGet } from "../../shared/api/client";

export type ServidorResumo = {
  id: number;
  nome: string;
  nome_social: string | null;
  cpf: string | null;
  email: string | null;
  ativo: boolean | null;
  admissao: string | null;
  tramitacao: string | null;
};

export type ProtocoloResumo = {
  id: number;
  data: string | null;
  situacao: string | null;
};

export type PericiaResumo = {
  id: number;
  protocolo_id: number;
  data: string | null;
  motivo: string | null;
  subjetivo: string | null;
  objetivo: string | null;
  conduta: string | null;
  relatorio: string | null;
  atestado: boolean;
  dias_atestado: number | null;
  cids: string[];
};

export type ServidorDetalhe = ServidorResumo & {
  nascimento: string | null;
  email: string | null;
  telefone: string | null;
  celular: string | null;
  protocolos: ProtocoloResumo[];
  historico_medico_visivel: boolean;
  pericias: PericiaResumo[];
};

export function buscarServidores(
  busca: string,
  signal?: AbortSignal,
): Promise<ServidorResumo[]> {
  const parametros = new URLSearchParams({ busca });
  return apiGet(`/api/v1/legado/servidores?${parametros}`, signal);
}

export function consultarServidor(
  servidorId: number,
  signal?: AbortSignal,
): Promise<ServidorDetalhe> {
  return apiGet(`/api/v1/legado/servidores/${servidorId}`, signal);
}
