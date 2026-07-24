export class ApiError extends Error {
  constructor(
    public readonly statusCode: number,
    message = "A API não conseguiu concluir a solicitação.",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  csrfToken?: string;
  signal?: AbortSignal;
};

export async function apiRequest<ResponseBody>(
  path: string,
  options: RequestOptions = {},
): Promise<ResponseBody> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.csrfToken) {
    headers["X-CSRFToken"] = options.csrfToken;
  }

  const response = await fetch(path, {
    method: options.method ?? "GET",
    credentials: "include",
    headers,
    body:
      options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  if (!response.ok) {
    let message: string | undefined;
    try {
      const errorBody = (await response.json()) as { detail?: string };
      message = errorBody.detail;
    } catch {
      message = undefined;
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as ResponseBody;
}

export function apiGet<ResponseBody>(
  path: string,
  signal?: AbortSignal,
): Promise<ResponseBody> {
  return apiRequest<ResponseBody>(path, { signal });
}

export function apiPost<ResponseBody>(
  path: string,
  body: unknown,
  csrfToken: string,
): Promise<ResponseBody> {
  return apiRequest<ResponseBody>(path, {
    method: "POST",
    body,
    csrfToken,
  });
}

export function apiPatch<ResponseBody>(
  path: string,
  body: unknown,
  csrfToken: string,
): Promise<ResponseBody> {
  return apiRequest<ResponseBody>(path, {
    method: "PATCH",
    body,
    csrfToken,
  });
}
