// src/application/managers/SearchManager.ts

import {ISearchManager} from './interfaces/ISearchManager.js';
import {IManager} from './interfaces/IManager.js';
import type {Graph} from '@core/index.js';

/**
 * Implements search-related operations for the knowledge graph.
 * Provides functionality for searching nodes and retrieving graph data.
 */
export class SearchManager extends IManager implements ISearchManager {
    /**
     * Searches for nodes in the knowledge graph based on a query.
     * Includes both matching nodes and their immediate neighbors.
     */
    async searchNodes(query: string): Promise<Graph> {
        try {
            this.emit('beforeSearch', {query});

            const graph = await this.storage.loadGraph();

            // Find directly matching nodes
            const matchingNodes = graph.nodes.filter(node =>
                node.name.toLowerCase().includes(query.toLowerCase()) ||
                node.nodeType.toLowerCase().includes(query.toLowerCase()) ||
                node.metadata.some(meta =>
                    meta.toLowerCase().includes(query.toLowerCase())
                )
            );

            // Get names of matching nodes for efficient lookup
            const matchingNodeNames = new Set(matchingNodes.map(node => node.name));

            // Find all edges connected to matching nodes
            const connectedEdges = graph.edges.filter(edge =>
                matchingNodeNames.has(edge.from) || matchingNodeNames.has(edge.to)
            );

            // Get names of all neighbor nodes from the edges
            const neighborNodeNames = new Set<string>();
            connectedEdges.forEach(edge => {
                if (matchingNodeNames.has(edge.from)) {
                    neighborNodeNames.add(edge.to);
                }
                if (matchingNodeNames.has(edge.to)) {
                    neighborNodeNames.add(edge.from);
                }
            });

            // Get all neighbor nodes
            const neighborNodes = graph.nodes.filter(node =>
                !matchingNodeNames.has(node.name) && neighborNodeNames.has(node.name)
            );

            // Combine matching nodes and their neighbors
            const resultNodes = [...matchingNodes, ...neighborNodes];

            const result: Graph = {
                nodes: resultNodes,
                edges: connectedEdges
            };

            this.emit('afterSearch', result);
            return result;
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Search operation failed: ${message}`);
        }
    }

    /**
     * Retrieves specific nodes and their immediate neighbors from the knowledge graph.
     */
    async openNodes(names: string[]): Promise<Graph> {
        try {
            this.emit('beforeOpenNodes', {names});

            const graph = await this.storage.loadGraph();

            // Get the requested nodes
            const requestedNodes = graph.nodes.filter(node =>
                names.includes(node.name)
            );

            // Get names of requested nodes for efficient lookup
            const requestedNodeNames = new Set(requestedNodes.map(node => node.name));

            // Find all edges connected to requested nodes
            const connectedEdges = graph.edges.filter(edge =>
                requestedNodeNames.has(edge.from) || requestedNodeNames.has(edge.to)
            );

            // Get names of all neighbor nodes from the edges
            const neighborNodeNames = new Set<string>();
            connectedEdges.forEach(edge => {
                if (requestedNodeNames.has(edge.from)) {
                    neighborNodeNames.add(edge.to);
                }
                if (requestedNodeNames.has(edge.to)) {
                    neighborNodeNames.add(edge.from);
                }
            });

            // Get all neighbor nodes
            const neighborNodes = graph.nodes.filter(node =>
                !requestedNodeNames.has(node.name) && neighborNodeNames.has(node.name)
            );

            // Combine requested nodes and their neighbors
            const resultNodes = [...requestedNodes, ...neighborNodes];

            const result: Graph = {
                nodes: resultNodes,
                edges: connectedEdges
            };

            this.emit('afterOpenNodes', result);
            return result;
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to open nodes: ${message}`);
        }
    }

    /**
     * Reads and returns the entire knowledge graph.
     */
    async readGraph(): Promise<Graph> {
        try {
            this.emit('beforeReadGraph', {});
            const graph = await this.storage.loadGraph();
            this.emit('afterReadGraph', graph);
            return graph;
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to read graph: ${message}`);
        }
    }

    /**
     * Initializes the search manager.
     */
    async initialize(): Promise<void> {
        try {
            await super.initialize();
            // Add any search-specific initialization here
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to initialize SearchManager: ${message}`);
        }
    }
}