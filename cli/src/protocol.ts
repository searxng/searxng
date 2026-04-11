/**
 * SearXNG CLI - Protocol Definitions
 * Standardized envelope format for CLI communication
 */

export type CliEnvelopeError = {
    code: string;
    message: string;
    retryable: boolean;
    details?: Record<string, unknown>;
};

export type CliEnvelope<T> = {
    status: 'ok' | 'error';
    data: T | null;
    error: CliEnvelopeError | null;
    hint: string | null;
};

export function createSuccessEnvelope<T>(data: T): CliEnvelope<T> {
    return {
        status: 'ok',
        data,
        error: null,
        hint: null
    };
}

export function createErrorEnvelope(
    code: string,
    message: string,
    options: {
        retryable?: boolean;
        details?: Record<string, unknown>;
        hint?: string | null;
    } = {}
): CliEnvelope<null> {
    return {
        status: 'error',
        data: null,
        error: {
            code,
            message,
            retryable: options.retryable ?? false,
            details: options.details
        },
        hint: options.hint ?? null
    };
}
