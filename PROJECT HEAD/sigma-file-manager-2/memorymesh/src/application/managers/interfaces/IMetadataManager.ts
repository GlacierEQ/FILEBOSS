// src/application/managers/interfaces/IMetadataManager.ts

import {IManager} from './IManager.js';
import type {Metadata, MetadataAddition, MetadataResult, MetadataDeletion} from '@core/index.js';

/**
 * Interface for metadata-related operations in the knowledge graph.
 * Defines the contract for managing metadata, including adding, deleting, and retrieving metadata for nodes.
 */
export interface IMetadataManager extends IManager {
    /**
     * Adds metadata to existing nodes.
     */
    addMetadata(metadata: MetadataAddition[]): Promise<MetadataResult[]>;

    /**
     * Deletes metadata from nodes.
     */
    deleteMetadata(deletions: MetadataDeletion[]): Promise<void>;

    /**
     * Retrieves metadata for a specific node.
     */
    getMetadata(nodeName: string): Promise<Metadata>;
}