/**
 * SearXNG CLI - Search Service
 */

import axios, { AxiosInstance } from 'axios';
import { HttpsProxyAgent } from 'https-proxy-agent';
import { config } from './config.js';

export interface SearchOptions {
    query: string;
    engines?: string[];
    categories?: string[];
    limit?: number;
    page?: number;
    language?: string;
    timeRange?: 'day' | 'week' | 'month' | 'year' | 'all';
    format?: 'json' | 'csv' | 'html';
}

export interface SearchResult {
    title: string;
    url: string;
    content: string;
    engine: string;
    category: string;
    publishedDate?: string;
    thumbnail?: string;
    score?: number;
}

export interface SearchResponse {
    query: string;
    numberOfResults: number;
    results: SearchResult[];
    suggestions: string[];
    answers: string[];
    corrections: string[];
    infoboxes: Array<{
        infobox: string;
        content: string;
        engine: string;
    }>;
    unresponsiveEngines: string[];
}

export class SearXNGService {
    private client: AxiosInstance;

    constructor() {
        const axiosConfig: any = {
            baseURL: config.baseUrl,
            timeout: config.timeout,
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'searxng-cli/1.0.0'
            }
        };

        if (config.useProxy && config.proxyUrl) {
            try {
                const proxyAgent = new HttpsProxyAgent(config.proxyUrl);
                axiosConfig.httpsAgent = proxyAgent;
                axiosConfig.httpAgent = proxyAgent;
            } catch (error) {
                console.error(`Failed to configure proxy: ${error instanceof Error ? error.message : String(error)}`);
            }
        }

        this.client = axios.create(axiosConfig);
    }

    async getEngines(): Promise<string[]> {
        try {
            const response = await this.client.get('/config');
            const engines = response.data.engines || [];
            return engines
                .filter((e: any) => e.enabled)
                .map((e: any) => e.name);
        } catch (error) {
            console.error(`Failed to fetch engines: ${error instanceof Error ? error.message : String(error)}`);
            return [];
        }
    }

    async getCategories(): Promise<string[]> {
        try {
            const response = await this.client.get('/config');
            const categories = response.data.categories || [];
            return categories.map((c: any) => typeof c === 'string' ? c : c?.name).filter(Boolean);
        } catch (error) {
            console.error(`Failed to fetch categories: ${error instanceof Error ? error.message : String(error)}`);
            return [];
        }
    }

    async search(options: SearchOptions): Promise<SearchResponse> {
        const params: Record<string, string> = {
            q: options.query,
            format: 'json'
        };

        if (options.engines && options.engines.length > 0) {
            params.engines = options.engines.join(',');
        }

        if (options.categories && options.categories.length > 0) {
            params.categories = options.categories.join(',');
        }

        if (options.language) {
            params.language = options.language;
        }

        if (options.timeRange) {
            params.time_range = options.timeRange;
        }

        if (options.page && options.page > 1) {
            params.pageno = String(options.page);
        }

        try {
            const response = await this.client.get('/search', { params });
            const data = response.data;

            const results: SearchResult[] = (data.results || []).map((item: any) => ({
                title: item.title || '',
                url: item.url || '',
                content: item.content || item.snippet || '',
                engine: item.engine || 'unknown',
                category: item.category || 'general',
                publishedDate: item.publishedDate,
                thumbnail: item.thumbnail,
                score: item.score
            }));

            const limitedResults = options.limit && options.limit > 0
                ? results.slice(0, options.limit)
                : results;

            return {
                query: data.query || options.query,
                numberOfResults: data.numberOfResults || limitedResults.length,
                results: limitedResults,
                suggestions: data.suggestions || [],
                answers: data.answers || [],
                corrections: data.corrections || [],
                infoboxes: data.infoboxes || [],
                unresponsiveEngines: data.unresponsive_engines || []
            };
        } catch (error) {
            if (axios.isAxiosError(error)) {
                throw new Error(`Search failed: ${error.response?.statusText || error.message}`);
            }
            throw error;
        }
    }

    async healthCheck(): Promise<{
        status: 'healthy' | 'unhealthy';
        baseUrl: string;
        engines?: string[];
        error?: string;
    }> {
        try {
            const response = await this.client.get('/healthz', { timeout: 5000 });
            const engines = await this.getEngines();
            return {
                status: 'healthy',
                baseUrl: config.baseUrl,
                engines
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                baseUrl: config.baseUrl,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }
}
