// src/tools/callToolHandler.ts

import {toolsRegistry, ToolHandlerFactory} from '@integration/index.js';
import {formatToolError} from '@shared/index.js';
import type {ApplicationManager} from '@application/index.js';
import type {ToolResponse} from '@shared/index.js';

interface ToolCallRequest {
    params: {
        name: string;
        arguments: Record<string, any>;
    };
}

/**
 * Handles incoming tool call requests by routing them to the appropriate handler
 */
export async function handleCallToolRequest(
    request: ToolCallRequest,
    knowledgeGraphManager: ApplicationManager
): Promise<ToolResponse> {
    try {
        const {name, arguments: args} = request.params;

        if (!args) {
            return formatToolError({
                operation: name,
                error: "Tool arguments are required",
                suggestions: ["Provide required arguments for the tool"]
            });
        }

        // Ensure tools registry is initialized
        if (!toolsRegistry.hasTool(name)) {
            return formatToolError({
                operation: name,
                error: `Tool not found: ${name}`,
                context: {
                    availableTools: toolsRegistry.getAllTools().map(t => t.name)
                },
                suggestions: ["Verify tool name is correct"],
                recoverySteps: ["Check available tools list"]
            });
        }

        // Initialize handlers if needed
        if (!ToolHandlerFactory.isInitialized()) {
            ToolHandlerFactory.initialize(knowledgeGraphManager);
        }

        // Get appropriate handler and process the request
        const handler = ToolHandlerFactory.getHandler(name);
        return await handler.handleTool(name, args);

    } catch (error) {
        return formatToolError({
            operation: "callTool",
            error: error instanceof Error ? error.message : 'Unknown error occurred',
            context: {request},
            suggestions: [
                "Verify tool name and arguments",
                "Check tool handler initialization"
            ],
            recoverySteps: [
                "Review tool documentation",
                "Ensure all required arguments are provided"
            ]
        });
    }
}