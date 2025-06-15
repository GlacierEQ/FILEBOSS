// src/types/events.ts

import {
    Edge,
    Graph,
    MetadataAddition,
    MetadataDeletion,
    MetadataResult
} from "@core/index.js";

/**
 * Event handler function type
 */
export type EventListener = (data?: any) => void;

/**
 * Map of event names to their listeners
 */
export interface EventMap {
    [eventName: string]: Set<EventListener>;
}

/**
 * Defines actions that can be rolled back during a transaction
 */
export interface RollbackAction {
    action: () => Promise<void>;
    description: string;
}

/**
 * Event emitter events
 */
export interface EmitterEvents {
    // Manager Initialization
    initialized: { manager: string };

    // Node Events
    beforeAddNodes: { nodes: Node[] };
    afterAddNodes: { nodes: Node[] };
    beforeUpdateNodes: { nodes: Node[] };
    afterUpdateNodes: { nodes: Node[] };
    beforeDeleteNodes: { nodeNames: string[] };
    afterDeleteNodes: { deletedCount: number };

    // Edge Events
    beforeAddEdges: { edges: Edge[] };
    afterAddEdges: { edges: Edge[] };
    beforeUpdateEdges: { edges: Edge[] };
    afterUpdateEdges: { edges: Edge[] };
    beforeDeleteEdges: { edges: Edge[] };
    afterDeleteEdges: { deletedCount: number };

    // Metadata Events
    beforeAddMetadata: { metadata: MetadataAddition[] };
    afterAddMetadata: { results: MetadataResult[] };
    beforeDeleteMetadata: { deletions: MetadataDeletion[] };
    afterDeleteMetadata: { deletedCount: number };

    // Search Events
    beforeSearch: { query: string };
    afterSearch: Graph;
    beforeOpenNodes: { names: string[] };
    afterOpenNodes: Graph;

    // Transaction Events
    beforeBeginTransaction: {};
    afterBeginTransaction: {};
    beforeCommit: {};
    afterCommit: {};
    beforeRollback: { actions: RollbackAction[] };
    afterRollback: {};

    // Error Event
    error: { operation: string; error: Error };
}