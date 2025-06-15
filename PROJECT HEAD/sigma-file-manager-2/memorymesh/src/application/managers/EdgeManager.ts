// src/application/managers/EdgeManager.ts

import {IEdgeManager} from '@application/managers/interfaces/IEdgeManager.js';
import {GraphValidator, EdgeWeightUtils} from '@core/index.js';
import type {Edge} from '@core/index.js';
import type {EdgeUpdate, EdgeFilter} from '@shared/index.js';

/**
 * Implements edge-related operations for the knowledge graph.
 * Includes adding, updating, deleting, and retrieving edges.
 */
export class EdgeManager extends IEdgeManager {
    /**
     * Adds new edges to the knowledge graph.
     */
    async addEdges(edges: Edge[]): Promise<Edge[]> {
        try {
            this.emit('beforeAddEdges', {edges});

            const graph = await this.storage.loadGraph();

            // Validate edge uniqueness and node existence using GraphValidator
            const newEdges = edges.filter(edge => {
                GraphValidator.validateEdgeUniqueness(graph, edge);
                // Ensure weights are set
                return EdgeWeightUtils.ensureWeight(edge);
            });

            if (newEdges.length === 0) {
                return [];
            }

            for (const edge of newEdges) {
                GraphValidator.validateNodeExists(graph, edge.from);
                GraphValidator.validateNodeExists(graph, edge.to);
            }

            graph.edges.push(...newEdges);
            await this.storage.saveGraph(graph);

            this.emit('afterAddEdges', {edges: newEdges});
            return newEdges;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(errorMessage);
        }
    }

    /**
     * Updates existing edges in the knowledge graph.
     */
    async updateEdges(edges: EdgeUpdate[]): Promise<Edge[]> {
        try {
            this.emit('beforeUpdateEdges', {edges});

            const graph = await this.storage.loadGraph();
            const updatedEdges: Edge[] = [];

            for (const updateEdge of edges) {
                const edgeIndex = graph.edges.findIndex(existing =>
                    existing.from === updateEdge.from &&
                    existing.to === updateEdge.to &&
                    existing.edgeType === updateEdge.edgeType
                );

                if (edgeIndex === -1) {
                    throw new Error(`Edge not found: ${updateEdge.from} -> ${updateEdge.to} (${updateEdge.edgeType})`);
                }

                // Validate node existence for updated nodes using GraphValidator
                if (updateEdge.newFrom) {
                    GraphValidator.validateNodeExists(graph, updateEdge.newFrom);
                }
                if (updateEdge.newTo) {
                    GraphValidator.validateNodeExists(graph, updateEdge.newTo);
                }

                const updatedEdge: Edge = {
                    type: 'edge',
                    from: updateEdge.newFrom || graph.edges[edgeIndex].from,
                    to: updateEdge.newTo || graph.edges[edgeIndex].to,
                    edgeType: updateEdge.newEdgeType || graph.edges[edgeIndex].edgeType,
                    weight: updateEdge.newWeight !== undefined ? updateEdge.newWeight : graph.edges[edgeIndex].weight
                };

                // Validate the new weight if it's being updated
                if (updatedEdge.weight !== undefined) {
                    EdgeWeightUtils.validateWeight(updatedEdge.weight);
                }

                graph.edges[edgeIndex] = updatedEdge;
                updatedEdges.push(updatedEdge);
            }

            await this.storage.saveGraph(graph);

            this.emit('afterUpdateEdges', {edges: updatedEdges});
            return updatedEdges;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(errorMessage);
        }
    }

    /**
     * Deletes edges from the knowledge graph.
     */
    async deleteEdges(edges: Edge[]): Promise<void> {
        try {
            this.emit('beforeDeleteEdges', {edges});

            const graph = await this.storage.loadGraph();
            const initialEdgeCount = graph.edges.length;

            graph.edges = graph.edges.filter(existing =>
                !edges.some(edge =>
                    existing.from === edge.from &&
                    existing.to === edge.to &&
                    existing.edgeType === edge.edgeType
                )
            );

            const deletedCount = initialEdgeCount - graph.edges.length;

            await this.storage.saveGraph(graph);

            this.emit('afterDeleteEdges', {deletedCount});
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(errorMessage);
        }
    }

    /**
     * Retrieves edges from the knowledge graph based on filter criteria.
     */
    async getEdges(filter?: EdgeFilter): Promise<Edge[]> {
        try {
            const graph = await this.storage.loadGraph();

            if (!filter || Object.keys(filter).length === 0) {
                return graph.edges;
            }

            return graph.edges.filter(edge => {
                if (filter.from && edge.from !== filter.from) return false;
                if (filter.to && edge.to !== filter.to) return false;
                return !(filter.edgeType && edge.edgeType !== filter.edgeType);
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(errorMessage);
        }
    }
}