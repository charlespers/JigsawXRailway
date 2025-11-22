import type { PartObject } from "./types";

export interface ComponentReasoning {
  componentId: string;
  componentName: string;
  reasoning: string;
  status: "reasoning" | "selected" | "validated";
  hierarchyLevel?: number;
}

export interface ComponentSelection {
  componentId: string;
  componentName: string;
  partData: PartObject;
  position?: {
    x: number;
    y: number;
  };
}

export interface ComponentAnalysisResponse {
  type: "reasoning" | "selection" | "complete" | "error" | "context_request";
  componentId?: string;
  componentName?: string;
  reasoning?: string;
  partData?: ComponentSelection["partData"];
  position?: ComponentSelection["position"];
  message?: string;
  hierarchyLevel?: number;
  queryId?: string;
  requestId?: string;
}

export interface ComponentAnalysisConfig {
  baseUrl: string;
  analysisEndpoint: string;
  timeout?: number;
}

import configService from "./config";

const defaultConfig: ComponentAnalysisConfig = {
  baseUrl: configService.getBackendUrl(),
  analysisEndpoint: "/mcp/component-analysis",
  timeout: configService.getTimeout(),
};


async function realStartAnalysis(
  query: string,
  provider: "openai" | "xai",
  config: ComponentAnalysisConfig,
  onUpdate: (update: ComponentAnalysisResponse) => void,
  signal?: AbortSignal,
  contextQueryId?: string,
  context?: string
): Promise<void> {
  const controller = signal ? undefined : new AbortController();
  const abortSignal = signal || controller?.signal;

  const timeoutId = config.timeout
    ? setTimeout(() => controller?.abort(), config.timeout)
    : null;

  try {
    const requestBody: {
      query: string;
      provider: "openai" | "xai";
      contextQueryId?: string;
      context?: string;
    } = { 
      query,
      provider: provider || "openai"
    };

    if (contextQueryId && context) {
      requestBody.contextQueryId = contextQueryId;
      requestBody.context = context;
    }

    const url = `${config.baseUrl}${config.analysisEndpoint}`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
      signal: abortSignal,
    });

    if (timeoutId) clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("Response body is not readable");
    }

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let eventEndIndex;
      while ((eventEndIndex = buffer.indexOf("\n\n")) !== -1) {
        const eventText = buffer.slice(0, eventEndIndex);
        buffer = buffer.slice(eventEndIndex + 2);

        const dataLine = eventText
          .split("\n")
          .find((line) => line.startsWith("data: "));
        if (dataLine) {
          try {
            const jsonText = dataLine.slice(6);
            const data: ComponentAnalysisResponse = JSON.parse(jsonText);
            
            // Log selection events for debugging
            if (data.type === "selection") {
              console.log(`[SSE] Selection event received:`, {
                componentId: data.componentId,
                componentName: data.componentName,
                partMpn: data.partData?.mpn
              });
            }
            
            onUpdate(data);

            if (data.type === "complete" || data.type === "error") {
              console.log(`[SSE] Stream ending with type: ${data.type}`);
              return;
            }
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }

    if (buffer.trim()) {
      const dataLine = buffer
        .split("\n")
        .find((line) => line.startsWith("data: "));
      if (dataLine) {
        try {
          const jsonText = dataLine.slice(6);
          const data: ComponentAnalysisResponse = JSON.parse(jsonText);
          onUpdate(data);
        } catch (e) {
          console.error("Failed to parse final SSE data:", e);
        }
      }
    }
  } catch (error: any) {
    if (timeoutId) clearTimeout(timeoutId);
    if (error.name === "AbortError") {
      throw new Error("Analysis timeout or cancelled");
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

class ComponentAnalysisService {
  private config: ComponentAnalysisConfig;
  private useMock: boolean;
  private currentAnalysis: AbortController | null = null;

  constructor(
    config?: Partial<ComponentAnalysisConfig>,
    useMock: boolean = false
  ) {
    this.config = { ...defaultConfig, ...config };
    this.useMock = useMock;
  }

  async startAnalysis(
    query: string,
    provider: "openai" | "xai" = "openai",
    onUpdate: (update: ComponentAnalysisResponse) => void,
    signal?: AbortSignal,
    contextQueryId?: string,
    context?: string
  ): Promise<void> {
    if (this.currentAnalysis) {
      this.currentAnalysis.abort();
    }

    const controller = signal ? undefined : new AbortController();
    this.currentAnalysis = controller ?? null;
    const abortSignal = signal || controller?.signal;

    try {
      // Mock mode removed - always use real API
      await realStartAnalysis(
        query,
        provider,
        this.config,
        onUpdate,
        abortSignal,
        contextQueryId,
        context
      );
    } catch (error: any) {
      if (error.name === "AbortError" || error.message?.includes("cancelled")) {
        onUpdate({
          type: "error",
          message: "Analysis cancelled",
        });
        return;
      }
      onUpdate({
        type: "error",
        message: error.message || "Analysis failed",
      });
      throw error;
    } finally {
      if (this.currentAnalysis === controller) {
        this.currentAnalysis = null;
      }
    }
  }

  cancelAnalysis(): void {
    if (this.currentAnalysis) {
      this.currentAnalysis.abort();
      this.currentAnalysis = null;
    }
  }

  updateConfig(config: Partial<ComponentAnalysisConfig>) {
    this.config = { ...this.config, ...config };
  }

  setUseMock(useMock: boolean) {
    this.useMock = useMock;
  }
}

export const componentAnalysisApi = new ComponentAnalysisService(
  {
    baseUrl: configService.getBackendUrl(),
  },
  false
);

export { ComponentAnalysisService };
