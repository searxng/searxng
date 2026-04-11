#!/usr/bin/env node
/**
 * SearXNG CLI - Main Entry Point
 */

import { runCli } from './runCli.js';
import { SearXNGService } from './service.js';

async function main() {
    const args = process.argv.slice(2);
    const service = new SearXNGService();

    try {
        const exitCode = await runCli(args, service);
        if (exitCode !== null) {
            process.exit(exitCode);
        }
    } catch (error) {
        console.error(`Fatal error: ${error instanceof Error ? error.message : String(error)}`);
        process.exit(1);
    }
}

main();
