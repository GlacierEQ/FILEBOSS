// src/utils/responseFormatter.ts

import type {
    ToolResponse,
    ToolResult,
    ToolResponseOptions,
    ToolErrorOptions,
    PartialSuccessOptions
} from '@shared/index.js';

/**
 * Formats successful tool responses in a consistent, AI-friendly way.
 */
export function formatToolResponse<T = any>({
                                                data,
                                                message,
                                                actionTaken,
                                                suggestions = []
                                            }: ToolResponseOptions<T>): ToolResponse<T> {
    const toolResult: ToolResult<T> = {
        isError: false,
        content: message ? [{type: "text", text: message}] : [],
        timestamp: new Date().toISOString()
    };

    if (data !== undefined) {
        toolResult.data = data;
    }

    if (actionTaken) {
        toolResult.actionTaken = actionTaken;
    }

    if (suggestions.length > 0) {
        toolResult.suggestions = suggestions;
    }

    return {toolResult};
}

/**
 * Formats error responses in a consistent, AI-friendly way.
 */
export function formatToolError({
                                    operation,
                                    error,
                                    context,
                                    suggestions = [],
                                    recoverySteps = []
                                }: ToolErrorOptions): ToolResponse {
    const toolResult: ToolResult = {
        isError: true,
        content: [
            {type: "text", text: `Error during ${operation}: ${error}`},
            ...(context ? [{type: "text", text: `Context: ${JSON.stringify(context)}`}] : [])
        ],
        timestamp: new Date().toISOString()
    };

    if (suggestions.length > 0) {
        toolResult.suggestions = suggestions;
    }

    if (recoverySteps.length > 0) {
        toolResult.recoverySteps = recoverySteps;
    }

    return {toolResult};
}

/**
 * Creates an informative message for partial success scenarios.
 */
export function formatPartialSuccess<T>({
                                            operation,
                                            attempted,
                                            succeeded,
                                            failed,
                                            details
                                        }: PartialSuccessOptions<T>): ToolResponse {
    const toolResult: ToolResult = {
        isError: true,
        content: [
            {
                type: "text",
                text: `Partial success for ${operation}: ${succeeded.length} succeeded, ${failed.length} failed`
            },
            {
                type: "text",
                text: `Details: ${JSON.stringify(details)}`
            }
        ],
        data: {
            succeededItems: succeeded,
            failedItems: failed.map(item => ({
                item,
                reason: details[String(item)] || 'Unknown error'
            }))
        },
        suggestions: [
            "Review failed items and their reasons",
            "Consider retrying failed operations individually",
            "Verify requirements for failed items"
        ],
        timestamp: new Date().toISOString()
    };

    return {toolResult};
}