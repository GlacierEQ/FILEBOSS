// src/core/graph/EdgeWeightUtils.ts

import type {Edge} from './Edge.js';

/**
 * Utility functions for working with edge weights in the knowledge graph
 */
export class EdgeWeightUtils {
    /**
     * Validates that a weight is within the valid range (0-1)
     */
    static validateWeight(weight: number): void {
        if (weight < 0 || weight > 1) {
            throw new Error('Edge weight must be between 0 and 1');
        }
    }

    /**
     * Sets a default weight for an edge if none is provided
     */
    static ensureWeight(edge: Edge): Edge {
        if (edge.weight === undefined) {
            return {
                ...edge,
                weight: 1 // Default to maximum weight
            };
        }
        return edge;
    }

    /**
     * Updates the weight of an edge based on new evidence
     * Uses a simple averaging approach
     */
    static updateWeight(currentWeight: number, newEvidence: number): number {
        this.validateWeight(newEvidence);
        return (currentWeight + newEvidence) / 2;
    }

    /**
     * Combines multiple edge weights (e.g., for parallel edges)
     * Uses the maximum weight by default
     */
    static combineWeights(weights: number[]): number {
        if (weights.length === 0) return 1;
        return Math.max(...weights);
    }
}