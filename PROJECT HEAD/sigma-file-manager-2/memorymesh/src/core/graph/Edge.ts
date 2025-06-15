// src/core/graph/Edge.ts

/**
 * Represents an edge connecting two nodes in the knowledge graph
 */
export interface Edge {
    type: 'edge';
    from: string;
    to: string;
    edgeType: string;
    weight?: number; // Optional weight property (0-1 range)
}