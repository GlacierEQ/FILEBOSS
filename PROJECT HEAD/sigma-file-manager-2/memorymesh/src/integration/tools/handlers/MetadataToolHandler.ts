// src/tools/handlers/MetadataToolHandler.ts

import {BaseToolHandler} from './BaseToolHandler.js';
import {formatToolResponse, formatToolError} from '@shared/index.js';
import type {ToolResponse} from '@shared/index.js';

export class MetadataToolHandler extends BaseToolHandler {
    async handleTool(name: string, args: Record<string, any>): Promise<ToolResponse> {
        try {
            this.validateArguments(args);

            switch (name) {
                case "add_metadata":
                    const addResult = await this.knowledgeGraphManager.addMetadata(args.metadata);
                    return formatToolResponse({
                        data: {metadata: addResult},
                        actionTaken: "Added metadata to nodes"
                    });

                case "delete_metadata":
                    await this.knowledgeGraphManager.deleteMetadata(args.deletions);
                    return formatToolResponse({
                        actionTaken: "Deleted metadata from nodes"
                    });

                default:
                    throw new Error(`Unknown metadata operation: ${name}`);
            }
        } catch (error) {
            return formatToolError({
                operation: name,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
                context: {args},
                suggestions: [
                    "Verify node existence",
                    "Check metadata format"
                ],
                recoverySteps: [
                    "Ensure nodes exist before adding metadata",
                    "Verify metadata content format"
                ]
            });
        }
    }
}