// src/application/managers/interfaces/INodeManager.ts

import {IManager} from './IManager.js';
import type {Node} from '@core/index.js';

/**
 * Interface for node-related operations in the knowledge graph.
 * Defines the contract for managing nodes, including adding, updating, deleting, and retrieving nodes.
 */
export interface INodeManager extends IManager {
    /**
     * Adds new nodes to the knowledge graph.
     */
    addNodes(nodes: Node[]): Promise<Node[]>;

    /**
     * Updates existing nodes in the knowledge graph.
     */
    updateNodes(nodes: Partial<Node>[]): Promise<Node[]>;

    /**
     * Deletes nodes from the knowledge graph.
     */
    deleteNodes(nodeNames: string[]): Promise<void>;

    /**
     * Retrieves specific nodes from the knowledge graph by their names.
     */
    getNodes(nodeNames: string[]): Promise<Node[]>;
}