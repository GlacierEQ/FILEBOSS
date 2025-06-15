// src/application/managers/interfaces/IEdgeManager.ts

import {IManager} from './IManager.js';
import type {EdgeUpdate, EdgeFilter} from '@shared/index.js';
import type {Edge} from '@core/index.js'

/**
 * Interface for edge-related operations in the knowledge graph.
 * Defines the contract for managing edges, including adding, updating, deleting, and retrieving edges.
 */
export abstract class IEdgeManager extends IManager {
    /**
     * Adds new edges to the knowledge graph.
     */
    abstract addEdges(edges: Edge[]): Promise<Edge[]>;

    /**
     * Updates existing edges in the knowledge graph.
     */
    abstract updateEdges(edges: EdgeUpdate[]): Promise<Edge[]>;

    /**
     * Deletes edges from the knowledge graph.
     */
    abstract deleteEdges(edges: Edge[]): Promise<void>;

    /**
     * Retrieves edges from the knowledge graph based on filter criteria.
     */
    abstract getEdges(filter?: EdgeFilter): Promise<Edge[]>;
}