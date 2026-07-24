export class ApiError extends Error {
  constructor(public readonly statusCode: number) {
    super("A API não conseguiu concluir a solicitação.");
    this.name = "ApiError";
  }
}

export async function apiGet<ResponseBody>(
  path: string,
  signal?: AbortSignal,
): Promise<ResponseBody> {
  const response = await fetch(path, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (!response.ok) {
    throw new ApiError(response.status);
  }

  return (await response.json()) as ResponseBody;
}
