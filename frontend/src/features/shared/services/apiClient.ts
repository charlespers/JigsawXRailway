/**
 * Standardized API Client
 * Enterprise-grade API client with interceptors, retry logic, and error handling
 */

import configService from './config';

export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export interface RequestOptions extends RequestInit {
  retries?: number;
  retryDelay?: number;
  timeout?: number;
}

class ApiClient {
  private config: ApiClientConfig;
  private interceptors: {
    request: Array<(config: RequestInit) => RequestInit | Promise<RequestInit>>;
    response: Array<(response: Response) => Response | Promise<Response>>;
    error: Array<(error: Error) => Error | Promise<Error>>;
  };

  constructor(config: ApiClientConfig) {
    this.config = {
      timeout: 30000,
      retries: 3,
      retryDelay: 1000,
      ...config,
    };
    
    this.interceptors = {
      request: [],
      response: [],
      error: [],
    };
  }

  updateConfig(config: Partial<ApiClientConfig>) {
    this.config = { ...this.config, ...config };
  }

  // Interceptor registration
  addRequestInterceptor(interceptor: (config: RequestInit) => RequestInit | Promise<RequestInit>) {
    this.interceptors.request.push(interceptor);
  }

  addResponseInterceptor(interceptor: (response: Response) => Response | Promise<Response>) {
    this.interceptors.response.push(interceptor);
  }

  addErrorInterceptor(interceptor: (error: Error) => Error | Promise<Error>) {
    this.interceptors.error.push(interceptor);
  }

  // Apply request interceptors
  private async applyRequestInterceptors(config: RequestInit): Promise<RequestInit> {
    let result = config;
    for (const interceptor of this.interceptors.request) {
      result = await interceptor(result);
    }
    return result;
  }

  // Apply response interceptors
  private async applyResponseInterceptors(response: Response): Promise<Response> {
    let result = response;
    for (const interceptor of this.interceptors.response) {
      result = await interceptor(result);
    }
    return result;
  }

  // Apply error interceptors
  private async applyErrorInterceptors(error: Error): Promise<Error> {
    let result = error;
    for (const interceptor of this.interceptors.error) {
      result = await interceptor(result);
    }
    return result;
  }

  // Retry logic with exponential backoff
  private async retryRequest(
    url: string,
    options: RequestOptions,
    attempt: number = 0
  ): Promise<Response> {
    const maxRetries = options.retries ?? this.config.retries ?? 3;
    const retryDelay = options.retryDelay ?? this.config.retryDelay ?? 1000;

    try {
      return await this.makeRequest(url, options);
    } catch (error: any) {
      // Don't retry on certain errors
      if (
        error.name === 'AbortError' ||
        (error.response && error.response.status >= 400 && error.response.status < 500 && error.response.status !== 408)
      ) {
        throw error;
      }

      if (attempt < maxRetries) {
        const delay = retryDelay * Math.pow(2, attempt); // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.retryRequest(url, options, attempt + 1);
      }
      throw error;
    }
  }

  // Make request with timeout
  private async makeRequest(url: string, options: RequestOptions): Promise<Response> {
    const timeout = options.timeout ?? this.config.timeout ?? 30000;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        (error as any).response = response;
        throw error;
      }
      
      return response;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        const timeoutError = new Error('Request timeout');
        timeoutError.name = 'TimeoutError';
        throw timeoutError;
      }
      throw error;
    }
  }

  // Main request method
  async request<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    // Apply request interceptors
    let requestConfig = await this.applyRequestInterceptors({
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    try {
      // Make request with retry logic
      const response = await this.retryRequest(url, requestConfig as RequestOptions);
      
      // Apply response interceptors
      const processedResponse = await this.applyResponseInterceptors(response);
      
      // Parse JSON response
      const contentType = processedResponse.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await processedResponse.json();
      }
      
      return processedResponse as any;
    } catch (error: any) {
      // Apply error interceptors
      const processedError = await this.applyErrorInterceptors(error);
      throw processedError;
    }
  }

  // Convenience methods
  async get<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  async patch<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

// Create singleton instance
const apiClient = new ApiClient({
  baseUrl: configService.getBackendUrl(),
});

// Add default error interceptor for logging
apiClient.addErrorInterceptor((error) => {
  console.error('[API Client] Request failed:', error);
  return error;
});

// Add default response interceptor for error handling
apiClient.addResponseInterceptor(async (response) => {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.clone().json();
      if (errorData.error || errorData.message) {
        errorMessage = errorData.error || errorData.message;
      }
    } catch {
      // Not JSON, use status text
    }
    const error = new Error(errorMessage);
    (error as any).response = response;
    throw error;
  }
  return response;
});

export default apiClient;

