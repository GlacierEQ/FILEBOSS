// src/core/graph/GraphValidator.ts

import type {Graph} from './Graph.js';
import type {Node} from './Node.js';
import type {Edge} from './Edge.js';
import {EdgeWeightUtils} from './EdgeWeightUtils.js';

/**
 * Provides validation methods for graph operations
 */
export class GraphValidator {
    /**
     * Validates that a node with the given name exists in the graph.
     */
    static validateNodeExists(graph: Graph, nodeName: string): void {
        if (!graph.nodes.some(node => node.name === nodeName)) {
            throw new Error(`Node not found: ${nodeName}`);
        }
    }

    /**
     * Validates that a node with the given name does not exist in the graph.
     */
    static validateNodeDoesNotExist(graph: Graph, nodeName: string): void {
        if (graph.nodes.some(node => node.name === nodeName)) {
            throw new Error(`Node already exists: ${nodeName}. Consider updating existing node.`);
        }
    }

    /**
     * Validates that an edge is unique in the graph.
     */
    static validateEdgeUniqueness(graph: Graph, edge: Edge): void {
        if (graph.edges.some(existing =>
            existing.from === edge.from &&
            existing.to === edge.to &&
            existing.edgeType === edge.edgeType
        )) {
            throw new Error(`Edge already exists: ${edge.from} -> ${edge.to} (${edge.edgeType})`);
        }
    }

    /**
     * Validates that a node has required properties.
     */
    static validateNodeProperties(node: Node): void {
        if (!node.name) {
            throw new Error("Node must have a 'name' property");
        }
        if (!node.nodeType) {
            throw new Error("Node must have a 'nodeType' property");
        }
        if (!Array.isArray(node.metadata)) {
            throw new Error("Node must have a 'metadata' array");
        }
    }

    /**
     * Validates that a partial node update has a name property.
     */
    static validateNodeNameProperty(node: Partial<Node>): void {
        if (!node.name) {
            throw new Error("Node must have a 'name' property for updating");
        }
    }

    /**
     * Validates that the provided value is a valid array of node names.
     */
    static validateNodeNamesArray(nodeNames: unknown): asserts nodeNames is string[] {
        if (!Array.isArray(nodeNames)) {
            throw new Error("nodeNames must be an array");
        }
        if (nodeNames.some(name => typeof name !== 'string')) {
            throw new Error("All node names must be strings");
        }
    }

    /**
     * Validates edge properties.
     */
    static validateEdgeProperties(edge: Edge): void {
        if (!edge.from) {
            throw new Error("Edge must have a 'from' property");
        }
        if (!edge.to) {
            throw new Error("Edge must have a 'to' property");
        }
        if (!edge.edgeType) {
            throw new Error("Edge must have an 'edgeType' property");
        }
        if (edge.weight !== undefined) {
            EdgeWeightUtils.validateWeight(edge.weight);
        }
    }

    /**
     * Validates that all referenced nodes in edges exist.
     */
    static validateEdgeReferences(graph: Graph, edges: Edge[]): void {
        for (const edge of edges) {
            this.validateNodeExists(graph, edge.from);
            this.validateNodeExists(graph, edge.to);
        }
    }

    /**
     * Validates the entire graph structure.
     */
    static validateGraphStructure(graph: Graph): void {
        if (!Array.isArray(graph.nodes)) {
            throw new Error("Graph must have a 'nodes' array");
        }
        if (!Array.isArray(graph.edges)) {
            throw new Error("Graph must have an 'edges' array");
        }

        // Validate all nodes
        graph.nodes.forEach(node => this.validateNodeProperties(node));

        // Validate all edges
        graph.edges.forEach(edge => {
            this.validateEdgeProperties(edge);
            this.validateNodeExists(graph, edge.from);
            this.validateNodeExists(graph, edge.to);
        });
    }
}

// Export convenience functions
export const {
    validateNodeExists,
    validateNodeDoesNotExist,
    validateEdgeUniqueness,
    validateNodeProperties,
    validateNodeNameProperty,
    validateNodeNamesArray,
    validateEdgeProperties,
    validateEdgeReferences,
    validateGraphStructure
} = GraphValidator;