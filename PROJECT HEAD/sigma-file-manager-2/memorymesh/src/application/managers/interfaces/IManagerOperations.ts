// src/application/managers/interfaces/IManagerOperations.ts

import type {
    Node,
    Edge,
    Metadata,
    Graph,
    MetadataAddition,
    MetadataResult,
    MetadataDeletion
} from '@core/index.js';
import type {
    EdgeUpdate,
    EdgeFilter
} from '@shared/index.js';

/**
 * Base interface for all manager operations
 */
export interface IManagerOperations {
    initialize(): Promise<void>;
}

/**
 * Node manager specific operations
 */
export interface INodeOperations extends IManagerOperations {
    addNodes(nodes: Node[]): Promise<Node[]>;

    updateNodes(nodes: Partial<Node>[]): Promise<Node[]>;

    deleteNodes(nodeNames: string[]): Promise<void>;

    getNodes(nodeNames: string[]): Promise<Node[]>;
}

/**
 * Edge manager specific operations
 */
export interface IEdgeOperations extends IManagerOperations {
    addEdges(edges: Edge[]): Promise<Edge[]>;

    updateEdges(edges: EdgeUpdate[]): Promise<Edge[]>;

    deleteEdges(edges: Edge[]): Promise<void>;

    getEdges(filter?: EdgeFilter): Promise<Edge[]>;
}

/**
 * Metadata manager specific operations
 */
export interface IMetadataOperations extends IManagerOperations {
    addMetadata(metadata: MetadataAddition[]): Promise<MetadataResult[]>;

    deleteMetadata(deletions: MetadataDeletion[]): Promise<void>;

    getMetadata(nodeName: string): Promise<Metadata>;
}

/**
 * Search manager specific operations
 */
export interface ISearchOperations extends IManagerOperations {
    searchNodes(query: string): Promise<Graph>;

    openNodes(names: string[]): Promise<Graph>;

    readGraph(): Promise<Graph>;
}