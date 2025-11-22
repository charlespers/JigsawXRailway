/**
 * Centralized configuration service for API endpoints and settings
 * All hardcoded URLs should be replaced with this service
 */

export interface AppConfig {
  backendUrl: string;
  apiVersion: string;
  timeout: number;
  enableLogging: boolean;
}

/**
 * Get backend URL from environment variables or default
 */
function getBackendUrl(): string {
  if (typeof window === "undefined") {
    return process.env.VITE_BACKEND_URL || "http://localhost:3001";
  }
  
  try {
    const env = (import.meta as any).env;
    return env?.VITE_BACKEND_URL || "http://localhost:3001";
  } catch {
    return "http://localhost:3001";
  }
}

/**
 * Get API version from environment or default to v1
 */
function getApiVersion(): string {
  if (typeof window === "undefined") {
    return process.env.VITE_API_VERSION || "v1";
  }
  
  try {
    const env = (import.meta as any).env;
    return env?.VITE_API_VERSION || "v1";
  } catch {
    return "v1";
  }
}

/**
 * Default configuration
 */
const defaultConfig: AppConfig = {
  backendUrl: getBackendUrl(),
  apiVersion: getApiVersion(),
  timeout: 60000,
  enableLogging: process.env.NODE_ENV === "development",
};

/**
 * Global configuration instance
 */
let globalConfig: AppConfig = { ...defaultConfig };

/**
 * Configuration service
 */
class ConfigService {
  private config: AppConfig;

  constructor(config?: Partial<AppConfig>) {
    this.config = { ...defaultConfig, ...config };
  }

  /**
   * Get the current configuration
   */
  getConfig(): AppConfig {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<AppConfig>): void {
    this.config = { ...this.config, ...updates };
  }

  /**
   * Get backend URL
   */
  getBackendUrl(): string {
    return this.config.backendUrl;
  }

  /**
   * Get API version
   */
  getApiVersion(): string {
    return this.config.apiVersion;
  }

  /**
   * Get full API base URL with version
   */
  getApiBaseUrl(): string {
    const base = this.config.backendUrl.replace(/\/$/, "");
    return `${base}/api/${this.config.apiVersion}`;
  }

  /**
   * Get timeout for requests
   */
  getTimeout(): number {
    return this.config.timeout;
  }

  /**
   * Check if logging is enabled
   */
  isLoggingEnabled(): boolean {
    return this.config.enableLogging;
  }

  /**
   * Validate configuration
   */
  validate(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!this.config.backendUrl) {
      errors.push("Backend URL is required");
    } else {
      try {
        new URL(this.config.backendUrl);
      } catch {
        errors.push("Backend URL is not a valid URL");
      }
    }

    if (this.config.timeout <= 0) {
      errors.push("Timeout must be greater than 0");
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

/**
 * Global config service instance
 */
export const configService = new ConfigService();

/**
 * Initialize configuration on module load
 */
if (typeof window !== "undefined") {
  // Re-validate and update from environment on client side
  const backendUrl = getBackendUrl();
  const apiVersion = getApiVersion();
  
  configService.updateConfig({
    backendUrl,
    apiVersion,
  });

  const validation = configService.validate();
  if (!validation.valid) {
    console.warn("Configuration validation errors:", validation.errors);
  }
}

export { ConfigService };
export default configService;

