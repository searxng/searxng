/**
 * SearXNG CLI - CLI Runner
 */

import { SearXNGService, SearchOptions } from './service.js';
import { createSuccessEnvelope, createErrorEnvelope } from './protocol.js';
import { config, VALID_CATEGORIES, COMMON_ENGINES } from './config.js';

const HELP_TEXT = `SearXNG CLI - Web Search Tool

Usage:
  searxng <query> [options]
  searxng --engines <engine1,engine2> <query>
  searxng --categories <category> <query>
  searxng --health

Options:
  -e, --engines <engines>      Comma-separated list of search engines
  -c, --categories <cats>      Comma-separated list of categories
  -l, --limit <n>              Maximum number of results (default: ${config.defaultLimit})
  -p, --page <n>               Page number for pagination
  --lang <code>                Language code (e.g., en, zh, ja)
  --time <range>               Time range: day, week, month, year, all
  -f, --format <fmt>           Output format: json, csv, html (default: json)
  --engines-list               List available search engines
  --categories-list            List available categories
  --health                     Check SearXNG server health
  -h, --help                   Show this help message

Examples:
  searxng "TypeScript tutorial"
  searxng --engines google,github "react hooks"
  searxng --categories it,science "machine learning"
  searxng --limit 5 --time week "latest news"

Environment Variables:
  SEARXNG_BASE_URL             SearXNG server URL
  SEARXNG_DEFAULT_ENGINE       Default search engine
  SEARXNG_ALLOWED_ENGINES      Comma-separated allowed engines
  SEARXNG_DEFAULT_LIMIT        Default result limit
  SEARXNG_USE_PROXY            Use proxy (true/false)
  SEARXNG_PROXY_URL            Proxy URL
  SEARXNG_TIMEOUT              Request timeout in ms
`;

interface CliOptions {
    query?: string;
    engines?: string[];
    categories?: string[];
    limit?: number;
    page?: number;
    language?: string;
    timeRange?: 'day' | 'week' | 'month' | 'year' | 'all';
    format?: 'json' | 'csv' | 'html';
    enginesList: boolean;
    categoriesList: boolean;
    health: boolean;
    help: boolean;
}

function parseArgs(args: string[]): CliOptions {
    const options: CliOptions = {
        enginesList: false,
        categoriesList: false,
        health: false,
        help: false
    };

    const positional: string[] = [];

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        switch (arg) {
            case '-h':
            case '--help':
                options.help = true;
                break;
            case '-e':
            case '--engines':
                options.engines = args[++i]?.split(',').map(e => e.trim()).filter(Boolean);
                break;
            case '-c':
            case '--categories':
                options.categories = args[++i]?.split(',').map(c => c.trim()).filter(Boolean);
                break;
            case '-l':
            case '--limit':
                options.limit = parseInt(args[++i], 10);
                break;
            case '-p':
            case '--page':
                options.page = parseInt(args[++i], 10);
                break;
            case '--lang':
                options.language = args[++i];
                break;
            case '--time':
                const timeVal = args[++i];
                if (['day', 'week', 'month', 'year', 'all'].includes(timeVal)) {
                    options.timeRange = timeVal as any;
                }
                break;
            case '-f':
            case '--format':
                const fmt = args[++i];
                if (['json', 'csv', 'html'].includes(fmt)) {
                    options.format = fmt as any;
                }
                break;
            case '--engines-list':
                options.enginesList = true;
                break;
            case '--categories-list':
                options.categoriesList = true;
                break;
            case '--health':
                options.health = true;
                break;
            default:
                if (!arg.startsWith('-')) {
                    positional.push(arg);
                }
                break;
        }
    }

    if (positional.length > 0) {
        options.query = positional.join(' ');
    }

    return options;
}

function formatAsCsv(results: any[]): string {
    if (results.length === 0) return '';

    const headers = ['title', 'url', 'content', 'engine', 'category'];
    const lines = [headers.join(',')];

    for (const r of results) {
        const row = headers.map(h => {
            const val = String(r[h] || '').replace(/"/g, '""');
            return `"${val}"`;
        });
        lines.push(row.join(','));
    }

    return lines.join('\n');
}

function formatAsHtml(results: any[]): string {
    const rows = results.map(r => `
        <tr>
            <td><a href="${r.url}">${r.title}</a></td>
            <td>${r.content}</td>
            <td>${r.engine}</td>
        </tr>
    `).join('');

    return `<!DOCTYPE html>
<html>
<head><title>Search Results</title></head>
<body>
<table border="1">
    <tr><th>Title</th><th>Content</th><th>Engine</th></tr>
    ${rows}
</table>
</body>
</html>`;
}

function formatOutput(data: any, format: 'json' | 'csv' | 'html'): string {
    switch (format) {
        case 'csv':
            return formatAsCsv(data.results || []);
        case 'html':
            return formatAsHtml(data.results || []);
        case 'json':
        default:
            return JSON.stringify(data, null, 2);
    }
}

export async function runCli(args: string[], service: SearXNGService): Promise<number | null> {
    const options = parseArgs(args);

    if (options.help) {
        console.log(HELP_TEXT);
        return 0;
    }

    if (options.health) {
        const health = await service.healthCheck();
        const envelope = health.status === 'healthy'
            ? createSuccessEnvelope(health)
            : createErrorEnvelope(
                'HEALTH_CHECK_FAILED',
                health.error || 'SearXNG server is not responding',
                { hint: `Check if SearXNG is running at ${config.baseUrl}` }
            );
        console.log(JSON.stringify(envelope, null, 2));
        return health.status === 'healthy' ? 0 : 1;
    }

    if (options.enginesList) {
        try {
            const engines = await service.getEngines();
            const envelope = createSuccessEnvelope({
                engines: engines.length > 0 ? engines : COMMON_ENGINES,
                source: engines.length > 0 ? 'server' : 'defaults'
            });
            console.log(JSON.stringify(envelope, null, 2));
            return 0;
        } catch (error) {
            const envelope = createErrorEnvelope(
                'ENGINES_FETCH_FAILED',
                error instanceof Error ? error.message : 'Failed to fetch engines',
                { hint: 'Showing common engines as fallback' }
            );
            console.log(JSON.stringify(envelope, null, 2));
            return 1;
        }
    }

    if (options.categoriesList) {
        try {
            const categories = await service.getCategories();
            const envelope = createSuccessEnvelope({
                categories: categories.length > 0 ? categories : VALID_CATEGORIES,
                source: categories.length > 0 ? 'server' : 'defaults'
            });
            console.log(JSON.stringify(envelope, null, 2));
            return 0;
        } catch (error) {
            const envelope = createErrorEnvelope(
                'CATEGORIES_FETCH_FAILED',
                error instanceof Error ? error.message : 'Failed to fetch categories',
                { hint: 'Showing valid categories as fallback' }
            );
            console.log(JSON.stringify(envelope, null, 2));
            return 1;
        }
    }

    if (!options.query) {
        const envelope = createErrorEnvelope(
            'MISSING_QUERY',
            'No search query provided',
            { hint: 'Use: searxng "your search query"' }
        );
        console.log(JSON.stringify(envelope, null, 2));
        return 1;
    }

    if (options.engines && config.allowedEngines.length > 0) {
        const invalid = options.engines.filter(e => !config.allowedEngines.includes(e));
        if (invalid.length > 0) {
            const envelope = createErrorEnvelope(
                'INVALID_ENGINES',
                `Engines not allowed: ${invalid.join(', ')}`,
                { hint: `Allowed engines: ${config.allowedEngines.join(', ')}` }
            );
            console.log(JSON.stringify(envelope, null, 2));
            return 1;
        }
    }

    const searchOptions: SearchOptions = {
        query: options.query,
        engines: options.engines,
        categories: options.categories,
        limit: options.limit ?? config.defaultLimit,
        page: options.page,
        language: options.language,
        timeRange: options.timeRange,
        format: options.format || 'json'
    };

    try {
        const results = await service.search(searchOptions);

        const envelope = createSuccessEnvelope({
            query: results.query,
            totalResults: results.numberOfResults,
            returnedResults: results.results.length,
            results: results.results,
            suggestions: results.suggestions,
            answers: results.answers,
            unresponsiveEngines: results.unresponsiveEngines
        });

        if (options.format && options.format !== 'json') {
            console.error(JSON.stringify(envelope, null, 2));
            console.log(formatOutput(results, options.format));
        } else {
            console.log(JSON.stringify(envelope, null, 2));
        }

        return 0;
    } catch (error) {
        const envelope = createErrorEnvelope(
            'SEARCH_FAILED',
            error instanceof Error ? error.message : 'Search request failed',
            {
                retryable: true,
                hint: 'Check your network connection and SearXNG server status'
            }
        );
        console.log(JSON.stringify(envelope, null, 2));
        return 1;
    }
}
