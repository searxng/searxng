/**
 * SearXNG CLI - Configuration
 *
 * Configuration priority (highest to lowest):
 * 1. Environment variables
 * 2. Config file (./sxng.config.json)
 * 3. Default values (localhost only)
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

export interface SearXNGConfig {
    baseUrl: string;
    defaultEngine: string;
    allowedEngines: string[];
    defaultLimit: number;
    useProxy: boolean;
    proxyUrl: string;
    timeout: number;
}

const DEFAULT_CONFIG: SearXNGConfig = {
    baseUrl: '',
    defaultEngine: '',
    allowedEngines: [],
    defaultLimit: 10,
    useProxy: false,
    proxyUrl: '',
    timeout: 10000
};

function readOptionalEnv(name: string, defaultValue?: string): string | undefined {
    const value = process.env[name]?.trim();
    return value ? value : defaultValue;
}

function readIntEnv(name: string, defaultValue: number): number {
    const value = process.env[name];
    if (!value) return defaultValue;
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : defaultValue;
}

function readBoolEnv(name: string, defaultValue: boolean): boolean {
    const value = process.env[name];
    if (value === undefined) return defaultValue;
    return value === 'true' || value === '1';
}

function findConfigFile(): string | null {
    const localConfig = './sxng.config.json';
    if (existsSync(localConfig)) {
        return localConfig;
    }
    return null;
}

function loadConfigFile(): Partial<SearXNGConfig> {
    const configPath = findConfigFile();
    if (!configPath) {
        return {};
    }

    try {
        const content = readFileSync(configPath, 'utf-8');
        const parsed = JSON.parse(content);
        return parsed;
    } catch {
        return {};
    }
}

function mergeConfig(): SearXNGConfig {
    const config: SearXNGConfig = { ...DEFAULT_CONFIG };

    const fileConfig = loadConfigFile();
    if (fileConfig.baseUrl !== undefined) config.baseUrl = fileConfig.baseUrl;
    if (fileConfig.defaultEngine !== undefined) config.defaultEngine = fileConfig.defaultEngine;
    if (fileConfig.allowedEngines !== undefined) config.allowedEngines = fileConfig.allowedEngines;
    if (fileConfig.defaultLimit !== undefined) config.defaultLimit = fileConfig.defaultLimit;
    if (fileConfig.useProxy !== undefined) config.useProxy = fileConfig.useProxy;
    if (fileConfig.proxyUrl !== undefined) config.proxyUrl = fileConfig.proxyUrl;
    if (fileConfig.timeout !== undefined) config.timeout = fileConfig.timeout;

    const envBaseUrl = readOptionalEnv('SEARXNG_BASE_URL');
    if (envBaseUrl) config.baseUrl = envBaseUrl;

    const envDefaultEngine = readOptionalEnv('SEARXNG_DEFAULT_ENGINE');
    if (envDefaultEngine !== undefined) config.defaultEngine = envDefaultEngine;

    const envAllowedEngines = process.env.SEARXNG_ALLOWED_ENGINES;
    if (envAllowedEngines !== undefined) {
        config.allowedEngines = envAllowedEngines.split(',').map(e => e.trim()).filter(Boolean);
    }

    const envDefaultLimit = process.env.SEARXNG_DEFAULT_LIMIT;
    if (envDefaultLimit !== undefined) {
        config.defaultLimit = readIntEnv('SEARXNG_DEFAULT_LIMIT', config.defaultLimit);
    }

    const envUseProxy = process.env.SEARXNG_USE_PROXY;
    if (envUseProxy !== undefined) {
        config.useProxy = readBoolEnv('SEARXNG_USE_PROXY', config.useProxy);
    }

    const envProxyUrl = readOptionalEnv('SEARXNG_PROXY_URL');
    if (envProxyUrl) config.proxyUrl = envProxyUrl;

    const envTimeout = process.env.SEARXNG_TIMEOUT;
    if (envTimeout !== undefined) {
        config.timeout = readIntEnv('SEARXNG_TIMEOUT', config.timeout);
    }

    return config;
}

export const config: SearXNGConfig = mergeConfig();

export const VALID_CATEGORIES = [
    'general',
    'images',
    'videos',
    'news',
    'it',
    'science',
    'music',
    'files',
    'books',
    'q&a',
    'social media',
    'weather',
    'map',
    'dictionaries',
    'translate'
];

export const COMMON_ENGINES = [
    'google', 'bing', 'duckduckgo', 'brave', 'startpage',
    'baidu', 'sogou', 'quark', '360search',
    'github', 'gitlab', 'npm', 'pypi', 'crates',
    'wikipedia', 'reddit', 'hackernews', 'stackoverflow',
    'arxiv', 'pubmed', 'google scholar'
];
