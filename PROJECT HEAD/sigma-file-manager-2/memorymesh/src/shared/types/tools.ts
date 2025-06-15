// src/types/tools.ts

/**
 * Schema definition for tool parameters
 */
export interface ToolSchema {
    type: string;
    properties: Record<string, SchemaProperty>;
    required?: string[];
}

/**
 * Property definition in a tool schema
 */
export interface SchemaProperty {
    type: string;
    description: string;
    items?: SchemaProperty;
    properties?: Record<string, SchemaProperty>;
    required?: string[];
    enum?: string[];
    minimum?: number;
    maximum?: number;
}

/**
 * Tool definition
 */
export interface Tool {
    name: string;
    description: string;
    inputSchema: ToolSchema;
}

/**
 * Content item in a tool result
 */
export interface ToolResultContent {
    type: string;
    text: string;
}

/**
 * Core result template that both success and error responses use
 */
export interface ToolResult<T = any> {
    isError: boolean;
    content: ToolResultContent[];  // For message display
    data?: T;
    actionTaken?: string;
    timestamp: string;
    suggestions?: string[];
    recoverySteps?: string[];
}

/**
 * Wrapper interface that matches the MCP server response format
 */
export interface ToolResponse<T = any> {
    toolResult: ToolResult<T>;
}

/**
 * Options for formatting a tool response
 */
export interface ToolResponseOptions<T = any> {
    data?: T;
    message?: string;
    actionTaken?: string;
    suggestions?: string[];
}

/**
 * Options for formatting a tool error
 */
export interface ToolErrorOptions {
    operation: string;
    error: string;
    context?: Record<string, any>;
    suggestions?: string[];
    recoverySteps?: string[];
}

/**
 * Options for formatting a partial success response
 */
export interface PartialSuccessOptions<T = any> {
    operation: string;
    attempted: T[];
    succeeded: T[];
    failed: T[];
    details: Record<string, string>;
}

/**
 * Request format for tool calls
 */
export interface ToolCallRequest {
    params: {
        name: string;
        arguments?: Record<string, any>;
    };
}