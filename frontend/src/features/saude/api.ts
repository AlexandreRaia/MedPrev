import { apiGet } from "../../shared/api/client";

export type HealthResponse = {
  status: "ok";
  service: string;
};

export function consultarSaudeDaApi(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/api/v1/health", signal);
}
