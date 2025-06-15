// src/types/operations.ts

import type {Node, Edge, Graph} from '@core/index.js';

/**
 * Edge update operation parameters
 */
export interface EdgeUpdate {
    from: string;
    to: string;
    edgeType: string;
    newFrom?: string;
    newTo?: string;
    newEdgeType?: string;
    newWeight?: number;
}

/**
 * Edge filter parameters
 */
export interface EdgeFilter {
    from?: string;
    to?: string;
    edgeType?: string;
}

/**
 * Metadata addition parameters
 */
export interface MetadataAddition {
    nodeName: string;
    contents: string[];
}

/**
 * Metadata deletion parameters
 */
export interface MetadataDeletion {
    nodeName: string;
    metadata: string[];
}

/**
 * Result of metadata operation
 */
export interface MetadataResult {
    nodeName: string;
    addedMetadata: string[];
}

/**
 * Result of getting edges
 */
export interface GetEdgesResult {
    edges: Edge[];
}

/**
 * Result of opening or searching nodes
 */
export interface OpenNodesResult {
    nodes: Node[];
    edges: Edge[];
}

// Operation Results
export interface GraphOperationResult {
    success: boolean;
    nodes?: Node[];
    edges?: Edge[];
    error?: string;
}

export interface SearchOperationResult {
    success: boolean;
    result?: Graph;
    error?: string;
}

export interface MetadataOperationResult {
    success: boolean;
    results?: MetadataResult[];
    error?: string;
}