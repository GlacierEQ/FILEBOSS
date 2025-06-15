// src/core/metadata/MetadataProcessor.ts

import {MetadataEntry, Metadata} from './Metadata.js';

export class MetadataProcessor {
    /**
     * Converts a raw metadata string to a structured entry
     */
    static parseMetadataEntry(entry: string): MetadataEntry {
        const colonIndex = entry.indexOf(':');
        if (colonIndex === -1) {
            throw new Error(`Invalid metadata format: ${entry}`);
        }

        return {
            key: entry.substring(0, colonIndex).trim(),
            value: entry.substring(colonIndex + 1).trim()
        };
    }

    /**
     * Formats a metadata entry into a string
     */
    static formatMetadataEntry(key: string, value: string | string[] | unknown): string {
        if (Array.isArray(value)) {
            return `${key}: ${value.join(', ')}`;
        }
        return `${key}: ${String(value)}`;
    }

    /**
     * Processes and validates metadata entries
     */
    static validateMetadata(metadata: Metadata): boolean {
        try {
            metadata.forEach(entry => this.parseMetadataEntry(entry));
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Merges multiple metadata arrays, removing duplicates
     */
    static mergeMetadata(...metadataArrays: Metadata[]): Metadata {
        const uniqueEntries = new Set<string>();

        metadataArrays.forEach(metadata => {
            metadata.forEach(entry => uniqueEntries.add(entry));
        });

        return Array.from(uniqueEntries);
    }

    /**
     * Filters metadata entries by key
     */
    static filterByKey(metadata: Metadata, key: string): Metadata {
        return metadata.filter(entry => {
            const parsed = this.parseMetadataEntry(entry);
            return parsed.key === key;
        });
    }

    /**
     * Extracts value for a specific metadata key
     */
    static getValue(metadata: Metadata, key: string): string | null {
        const entries = this.filterByKey(metadata, key);
        if (entries.length === 0) return null;

        return this.parseMetadataEntry(entries[0]).value;
    }

    /**
     * Creates a metadata entry map for efficient lookup
     */
    static createMetadataMap(metadata: Metadata): Map<string, string> {
        const map = new Map<string, string>();

        metadata.forEach(entry => {
            const {key, value} = this.parseMetadataEntry(entry);
            map.set(key, value);
        });

        return map;
    }
}