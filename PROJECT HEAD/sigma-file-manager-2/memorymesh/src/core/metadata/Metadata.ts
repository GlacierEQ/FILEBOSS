// src/core/metadata/Metadata.ts

/**
 * Represents metadata information associated with a node
 * Each string in the array represents a metadata entry in the format "key: value"
 */
export type Metadata = string[];

export interface MetadataEntry {
    key: string;
    value: string;
}

export interface MetadataAddition {
    nodeName: string;
    contents: string[];
}

export interface MetadataDeletion {
    nodeName: string;
    metadata: string[];
}

export interface MetadataResult {
    nodeName: string;
    addedMetadata: string[];
}