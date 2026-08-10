import { apiGet } from "../../shared/api/client";

export type GrupoCidIndicador = {
  codigo: string;
  ocorrencias: number;
};

export type Indicadores = {
  servidores_acompanhados: number;
  pericias_60_dias: number;
  pareceres_em_rascunho: number;
  pericias_com_atestado_60_dias: number;
  grupos_cid: GrupoCidIndicador[];
  solicitacoes_apoio_abertas: number;
  minhas_solicitacoes_pendentes: number | null;
  pareceres_concluidos: number;
  solicitacoes_apoio_respondidas: number;
};

export function consultarIndicadores(signal?: AbortSignal): Promise<Indicadores> {
  return apiGet("/api/v1/indicadores", signal);
}
