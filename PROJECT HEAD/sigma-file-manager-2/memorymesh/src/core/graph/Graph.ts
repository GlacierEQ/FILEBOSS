// src/core/graph/Graph.ts

import type {Node} from './Node.js';
import type {Edge} from './Edge.js';

/**
 * Represents the complete knowledge graph structure
 */
export interface Graph {
    nodes: Node[];
    edges: Edge[];
}