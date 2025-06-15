// src/tools/handlers/GraphToolHandler.ts

import {BaseToolHandler} from './BaseToolHandler.js';
import {formatToolResponse, formatToolError} from '@shared/index.js';
import type {ToolResponse} from '@shared/index.js';

export class GraphToolHandler extends BaseToolHandler {
    async handleTool(name: string, args: Record<string, any>): Promise<ToolResponse> {
        try {
            this.validateArguments(args);

            switch (name) {
                case "add_nodes":
                    const addedNodes = await this.knowledgeGraphManager.addNodes(args.nodes);
                    return formatToolResponse({
                        data: {nodes: addedNodes},
                        actionTaken: "Added nodes to knowledge graph"
                    });

                case "update_nodes":
                    const updatedNodes = await this.knowledgeGraphManager.updateNodes(args.nodes);
                    return formatToolResponse({
                        data: {nodes: updatedNodes},
                        actionTaken: "Updated nodes in knowledge graph"
                    });

                case "add_edges":
                    const addedEdges = await this.knowledgeGraphManager.addEdges(args.edges);
                    return formatToolResponse({
                        data: {edges: addedEdges},
                        actionTaken: "Added edges to knowledge graph"
                    });

                case "update_edges":
                    const updatedEdges = await this.knowledgeGraphManager.updateEdges(args.edges);
                    return formatToolResponse({
                        data: {edges: updatedEdges},
                        actionTaken: "Updated edges in knowledge graph"
                    });

                case "delete_nodes":
                    await this.knowledgeGraphManager.deleteNodes(args.nodeNames);
                    return formatToolResponse({
                        actionTaken: `Deleted nodes: ${args.nodeNames.join(', ')}`
                    });

                case "delete_edges":
                    await this.knowledgeGraphManager.deleteEdges(args.edges);
                    return formatToolResponse({
                        actionTaken: "Deleted edges from knowledge graph"
                    });

                default:
                    throw new Error(`Unknown graph operation: ${name}`);
            }
        } catch (error) {
            return formatToolError({
                operation: name,
                error: error instanceof Error ? error.message : 'Unknown error occurred',
                context: {args},
                suggestions: [
                    "Verify node/edge existence",
                    "Check input parameters format"
                ],
                recoverySteps: [
                    "Review the error details and adjust inputs",
                    "Ensure referenced nodes exist before creating edges"
                ]
            });
        }
    }
}