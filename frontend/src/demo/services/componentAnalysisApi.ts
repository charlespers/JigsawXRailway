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

const defaultConfig: ComponentAnalysisConfig = {
  baseUrl: "http://localhost:3001",
  analysisEndpoint: "/mcp/component-analysis",
  timeout: 60000,
};

export const MOCK_CONFIG = {
  enableLogging: false,
  reasoningDelay: 2000,
  selectionDelay: 5000,
  reasoningCount: { min: 2, max: 4 },
};

const mockComponents = [
  {
    id: "mcu",
    name: "Microcontroller",
    hierarchy: 0,
    reasoning: [
      "Analyzing project requirements: need WiFi/BT, sufficient GPIO, and low power consumption",
      "Comparing ESP32-S3 vs ESP32-C3: ESP32-S3 offers better performance and more pins",
      "Checking availability: ESP32-S3-WROOM-1 is in stock at multiple suppliers",
      "Validating compatibility: 3.3V operation matches power supply design",
    ],
    partData: {
      mpn: "ESP32-S3-WROOM-1-N8R2",
      manufacturer: "Espressif Systems",
      description:
        "WiFi and Bluetooth 5.0 enabled 32-bit microcontroller with dual-core processor",
      price: 2.89,
      currency: "USD",
      voltage: "3.0V ~ 3.6V",
      package: "48-QFN",
      interfaces: ["I2C", "SPI", "UART", "WiFi", "Bluetooth 5.0"],
      datasheet:
        "https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf",
      quantity: 1,
    },
    position: { x: 300, y: 200 },
  },
  {
    id: "power",
    name: "Power Management",
    hierarchy: 1,
    reasoning: [
      "Calculating power budget: MCU needs 3.3V @ 240mA, sensors need 3.3V @ 50mA",
      "USB-C input is 5V, need LDO regulator with 600mA capacity",
      "AP2112K-3.3 provides 600mA with low dropout voltage",
      "Checking thermal performance: AP2112K handles 600mA without overheating",
    ],
    partData: {
      mpn: "AP2112K-3.3TRG1",
      manufacturer: "Diodes Incorporated",
      description: "600mA low dropout voltage regulator with enable pin",
      price: 0.45,
      currency: "USD",
      voltage: "2.5V ~ 6.0V input, 3.3V output",
      package: "SOT-25",
      interfaces: [],
      datasheet: "https://www.diodes.com/assets/Datasheets/AP2112.pdf",
      quantity: 1,
    },
    position: { x: 200, y: 220 },
  },
  {
    id: "sensors",
    name: "Temperature Sensor",
    hierarchy: 1,
    reasoning: [
      "Project requires temperature and humidity sensing with high accuracy",
      "BME280 provides temperature, humidity, and pressure in single package",
      "I2C interface compatible with ESP32-S3, only needs 2 GPIO pins",
      "Validating accuracy: ±3% RH and ±1°C meets project requirements",
    ],
    partData: {
      mpn: "BME280",
      manufacturer: "Bosch Sensortec",
      description:
        "Digital humidity, pressure and temperature sensor with I2C and SPI interfaces",
      price: 3.95,
      currency: "USD",
      voltage: "1.71V ~ 3.6V",
      package: "LGA-8",
      interfaces: ["I2C", "SPI"],
      datasheet:
        "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf",
      quantity: 1,
    },
    position: { x: 400, y: 220 },
  },
  {
    id: "memory",
    name: "Flash Memory",
    hierarchy: 2,
    reasoning: [
      "ESP32-S3 has 8MB flash, but project needs additional storage for data logging",
      "W25Q128 provides 16MB SPI flash with fast read/write speeds",
      "SPI interface uses 4 pins, compatible with ESP32-S3 SPI peripheral",
      "Verifying endurance: 100K write cycles sufficient for logging application",
    ],
    partData: {
      mpn: "W25Q128JVSIQ",
      manufacturer: "Winbond Electronics",
      description: "128M-bit serial flash memory with SPI interface",
      price: 1.25,
      currency: "USD",
      voltage: "2.7V ~ 3.6V",
      package: "SOIC-8",
      interfaces: ["SPI"],
      datasheet:
        "https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf",
      quantity: 1,
    },
    position: { x: 300, y: 120 },
  },
  {
    id: "antenna",
    name: "WiFi Antenna",
    hierarchy: 2,
    reasoning: [
      "ESP32-S3 requires external antenna for optimal WiFi/BT range",
      "Ceramic chip antenna provides good performance in compact form factor",
      "ANT-2.4-CHP-T tuned for 2.4GHz ISM band with 2dBi gain",
      "Placement verified: antenna position optimized for RF performance",
    ],
    partData: {
      mpn: "ANT-2.4-CHP-T",
      manufacturer: "Antenova",
      description:
        "2.4GHz ceramic chip antenna with 2dBi gain for WiFi and Bluetooth applications",
      price: 0.85,
      currency: "USD",
      voltage: "N/A",
      package: "Chip",
      interfaces: [],
      datasheet: "https://www.antenova.com/datasheets/ANT-2.4-CHP-T.pdf",
      quantity: 1,
    },
    position: { x: 380, y: 150 },
  },
  {
    id: "passives",
    name: "Passives & Caps",
    hierarchy: 3,
    reasoning: [
      "Decoupling capacitors needed: 100nF for each IC power pin, 10µF bulk capacitor",
      "0603 package size provides good balance of size and capacitance",
      "X7R dielectric suitable for temperature range and voltage rating",
      "Calculating total: 8x 100nF + 2x 10µF = 10 capacitors total",
    ],
    partData: {
      mpn: "0603-X7R-100nF-50V",
      manufacturer: "Generic",
      description: "100nF X7R ceramic capacitor in 0603 package, 50V rating",
      price: 0.12,
      currency: "USD",
      voltage: "50V",
      package: "0603",
      interfaces: [],
      quantity: 10,
    },
    position: { x: 220, y: 150 },
  },
  {
    id: "connector",
    name: "USB-C Connector",
    hierarchy: 3,
    reasoning: [
      "USB-C connector needed for power input and programming interface",
      "USB4105-GF-A provides USB 2.0 data and 5V power in compact package",
      "24-pin connector with proper mechanical retention",
      "Verifying compatibility: matches ESP32-S3 USB-C design guidelines",
    ],
    partData: {
      mpn: "USB4105-GF-A",
      manufacturer: "GCT",
      description:
        "USB Type-C connector with 24 pins, USB 2.0 data and 5V power",
      price: 0.65,
      currency: "USD",
      voltage: "5V",
      package: "SMT",
      interfaces: ["USB 2.0"],
      datasheet: "https://gct.co/files/drawings/usb4105.pdf",
      quantity: 1,
    },
    position: { x: 250, y: 300 },
  },
];

const waitWithAbort = (
  duration: number,
  signal?: AbortSignal
): Promise<void> => {
  if (duration <= 0) {
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const cleanup = () => {
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      if (signal) {
        signal.removeEventListener("abort", onAbort);
      }
    };

    const onAbort = () => {
      cleanup();
      resolve();
    };

    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
      if (signal.aborted) {
        onAbort();
        return;
      }
    }

    timeoutId = setTimeout(() => {
      cleanup();
      resolve();
    }, duration);
  });
};

async function mockStartAnalysis(
  _query: string,
  _config: ComponentAnalysisConfig,
  onUpdate: (update: ComponentAnalysisResponse) => void,
  _signal?: AbortSignal,
  contextQueryId?: string,
  _context?: string
): Promise<void> {
  if (!contextQueryId && Math.random() < 0.1) {
    const testQueryId = `query_${Date.now()}`;
    onUpdate({
      type: "context_request",
      queryId: testQueryId,
      message:
        "I need more information about your power requirements. What is your target voltage range?",
    });
    return;
  }

  for (let i = 0; i < mockComponents.length; i++) {
    if (signal?.aborted) {
      throw new Error("Analysis cancelled");
    }

    const component = mockComponents[i];
    const reasoningCount =
      Math.floor(
        Math.random() *
          (MOCK_CONFIG.reasoningCount.max - MOCK_CONFIG.reasoningCount.min + 1)
      ) + MOCK_CONFIG.reasoningCount.min;

    for (let j = 0; j < reasoningCount; j++) {
      if (signal?.aborted) {
        throw new Error("Analysis cancelled");
      }

      await waitWithAbort(MOCK_CONFIG.reasoningDelay, signal);

      if (signal?.aborted) {
        throw new Error("Analysis cancelled");
      }

      const reasoningSnippet =
        component.reasoning[j] ||
        component.reasoning[
          Math.floor(Math.random() * component.reasoning.length)
        ];

      onUpdate({
        type: "reasoning",
        componentId: component.id,
        componentName: component.name,
        reasoning: reasoningSnippet,
        hierarchyLevel: component.hierarchy,
      });
    }

    if (signal?.aborted) {
      throw new Error("Analysis cancelled");
    }

    await waitWithAbort(MOCK_CONFIG.selectionDelay, signal);

    if (signal?.aborted) {
      throw new Error("Analysis cancelled");
    }

    onUpdate({
      type: "selection",
      componentId: component.id,
      componentName: component.name,
      partData: component.partData,
      position: component.position,
      hierarchyLevel: component.hierarchy,
    });
  }

  if (signal?.aborted) {
    throw new Error("Analysis cancelled");
  }

  await waitWithAbort(500, signal);

  if (signal?.aborted) {
    throw new Error("Analysis cancelled");
  }

  onUpdate({
    type: "complete",
    message:
      "Component analysis complete. All components validated and optimized.",
  });
}

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
            onUpdate(data);

            if (data.type === "complete" || data.type === "error") {
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
    useMock: boolean = true
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
      if (this.useMock) {
        await mockStartAnalysis(
          query,
          this.config,
          onUpdate,
          abortSignal,
          contextQueryId,
          context
        );
      } else {
        await realStartAnalysis(
          query,
          provider,
          this.config,
          onUpdate,
          abortSignal,
          contextQueryId,
          context
        );
      }
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
    baseUrl:
      typeof window !== "undefined"
        ? (import.meta as any).env?.VITE_BACKEND_URL ||
          "http://localhost:3001"
        : "http://localhost:3001",
  },
  false
);

export { ComponentAnalysisService };
