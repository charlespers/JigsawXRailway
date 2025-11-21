export interface DesignQueryRequest {
  query: string;
}

export interface DesignQueryResponse {
  type: "response" | "context_request";
  queryId?: string;
  requestId?: string;
  message: string;
  response?: string;
}

export interface DesignContinueRequest {
  context: string;
  queryId: string;
}

export interface DesignContinueResponse {
  type: "response" | "context_request";
  queryId?: string;
  requestId?: string;
  message: string;
  response?: string;
}

export interface DesignApiConfig {
  baseUrl: string;
  queryEndpoint: string;
  continueEndpoint: string;
  timeout?: number;
}

const defaultConfig: DesignApiConfig = {
  baseUrl: "http://localhost:3001",
  queryEndpoint: "/design/query",
  continueEndpoint: "/design/continue",
  timeout: 30000,
};

let mockQueryIdCounter = 0;
const mockActiveQueries = new Map<
  string,
  { query: string; timestamp: number }
>();

async function mockQuery(
  request: DesignQueryRequest,
  _config: DesignApiConfig
): Promise<DesignQueryResponse> {
  await new Promise((resolve) =>
    setTimeout(resolve, 9000 + Math.random() * 11000)
  );

  const queryId = `query_${++mockQueryIdCounter}_${Date.now()}`;
  mockActiveQueries.set(queryId, {
    query: request.query,
    timestamp: Date.now(),
  });

  const shouldRequestContext = Math.random() > 0.5;

  if (shouldRequestContext) {
    return {
      type: "context_request",
      queryId,
      message: `I need more information to process your query: "${request.query}". Please provide additional context about your requirements.`,
    };
  } else {
    mockActiveQueries.delete(queryId);
    return {
      type: "response",
      message: `Response to: "${request.query}" failed. We are out of credits for one of our spec sheet provides. We are waiting to hear back to extend limits`,
    };
  }
}

async function mockContinue(
  request: DesignContinueRequest,
  config: DesignApiConfig
): Promise<DesignContinueResponse> {
  await new Promise((resolve) =>
    setTimeout(resolve, 9000 + Math.random() * 11000)
  );

  const queryData = mockActiveQueries.get(request.queryId);
  if (!queryData) {
    throw new Error("Query ID not found. It may have expired.");
  }

  const shouldRequestMoreContext = Math.random() > 0.7;

  if (shouldRequestMoreContext) {
    return {
      type: "context_request",
      queryId: request.queryId,
      message: `Thank you for the context. I need one more piece of information: What is your preferred budget range?`,
    };
  } else {
    mockActiveQueries.delete(request.queryId);
    return {
      type: "response",
      message: `Thank you for providing the context. Based on your query "${queryData.query}" and the context you provided, here is the final response.`,
    };
  }
}

async function realQuery(
  request: DesignQueryRequest,
  config: DesignApiConfig,
  signal?: AbortSignal
): Promise<DesignQueryResponse> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;

  const timeoutId = config.timeout
    ? setTimeout(() => controller?.abort(), config.timeout)
    : null;

  try {
    const url = `${config.baseUrl}${config.queryEndpoint}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const data: DesignQueryResponse = await response.json();
    return data;
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error("Request timeout or cancelled");
    }
    if (
      error.message?.includes("Failed to fetch") ||
      error.name === "TypeError"
    ) {
      const isConnectionRefused =
        error.message?.includes("ERR_CONNECTION_REFUSED") ||
        error.message?.includes("Connection refused");

      if (isConnectionRefused) {
        throw new Error(
          `Backend server at ${config.baseUrl} is not running. Please start your design backend server.`
        );
      } else {
        throw new Error(
          `Failed to connect to design server at ${config.baseUrl}. Make sure the backend is running and CORS is configured.`
        );
      }
    }
    throw error;
  }
}

async function realContinue(
  request: DesignContinueRequest,
  config: DesignApiConfig,
  signal?: AbortSignal
): Promise<DesignContinueResponse> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;

  const timeoutId = config.timeout
    ? setTimeout(() => controller?.abort(), config.timeout)
    : null;

  try {
    const url = `${config.baseUrl}${config.continueEndpoint}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const data: DesignContinueResponse = await response.json();
    return data;
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error("Request timeout or cancelled");
    }
    if (
      error.message?.includes("Failed to fetch") ||
      error.name === "TypeError"
    ) {
      const isConnectionRefused =
        error.message?.includes("ERR_CONNECTION_REFUSED") ||
        error.message?.includes("Connection refused");

      if (isConnectionRefused) {
        throw new Error(
          `Backend server at ${config.baseUrl} is not running. Please start your design backend server.`
        );
      } else {
        throw new Error(
          `Failed to connect to design server at ${config.baseUrl}. Make sure the backend is running and CORS is configured.`
        );
      }
    }
    throw error;
  }
}

class DesignApiService {
  private config: DesignApiConfig;
  private useMock: boolean;

  constructor(config?: Partial<DesignApiConfig>, useMock: boolean = true) {
    this.config = { ...defaultConfig, ...config };
    this.useMock = useMock;
  }

  /**
   * @deprecated Design query/continue endpoints do not exist in the demo backend.
   * Use componentAnalysisApi.startAnalysis() instead to trigger component analysis.
   */
  async sendQuery(
    _query: string,
    _signal?: AbortSignal
  ): Promise<DesignQueryResponse> {
    console.warn(
      "Design query endpoint is not available in the demo backend. " +
      "Use componentAnalysisApi.startAnalysis() instead."
    );
    throw new Error(
      "Design query endpoint not available. Use component analysis API instead."
    );
  }

  /**
   * @deprecated Design continue endpoint does not exist in the demo backend.
   * Context handling is integrated into component analysis API.
   */
  async sendContext(
    _context: string,
    _queryId: string,
    _signal?: AbortSignal
  ): Promise<DesignContinueResponse> {
    console.warn(
      "Design continue endpoint is not available in the demo backend. " +
      "Context handling is integrated into component analysis API."
    );
    throw new Error(
      "Design continue endpoint not available. Context handling is integrated into component analysis API."
    );
  }

  updateConfig(config: Partial<DesignApiConfig>) {
    this.config = { ...this.config, ...config };
  }

  setUseMock(useMock: boolean) {
    this.useMock = useMock;
  }
}

function getDesignServerUrl(): string {
  if (typeof window === "undefined") {
    return "http://localhost:3001";
  }
  try {
    const url = import.meta.env?.VITE_BACKEND_URL || import.meta.env?.VITE_DESIGN_SERVER_URL || "http://localhost:3001";
    return url;
  } catch {
    return "http://localhost:3001";
  }
}

export const designApi = new DesignApiService(
  {
    baseUrl: getDesignServerUrl(),
  },
  false
);

export { DesignApiService };
