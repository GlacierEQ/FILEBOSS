// src/schema/loader/schemaLoader.ts

import {promises as fs} from 'fs';
import {SchemaBuilder} from './SchemaBuilder.js';
import path from 'path';
import {CONFIG} from '@config/index.js';

interface RawSchemaProperty {
    type: string;
    description: string;
    required?: boolean;
    enum?: string[];
    relationship?: {
        edgeType: string;
        description: string;
        nodeType?: string;
    };
}

interface RawSchema {
    name: string;
    description: string;
    properties: Record<string, RawSchemaProperty>;
    additionalProperties?: boolean;
}

/**
 * Responsible for loading and converting schema definitions from JSON files into SchemaBuilder instances.
 */
export class SchemaLoader {
    /**
     * Loads a specific schema by name.
     */
    static async loadSchema(schemaName: string): Promise<SchemaBuilder> {
        const SCHEMAS_DIR = CONFIG.PATHS.SCHEMAS_DIR;
        const schemaPath = path.join(SCHEMAS_DIR, `${schemaName}.schema.json`);

        try {
            const schemaContent = await fs.readFile(schemaPath, 'utf-8');
            const schema = JSON.parse(schemaContent) as RawSchema;
            this.validateSchema(schema);
            return this.convertToSchemaBuilder(schema);
        } catch (error) {
            if (error instanceof Error) {
                throw new Error(`Failed to load schema ${schemaName}: ${error.message}`);
            }
            throw new Error(`Failed to load schema ${schemaName}`);
        }
    }

    /**
     * Converts a JSON schema object into a SchemaBuilder instance.
     */
    static convertToSchemaBuilder(schema: RawSchema): SchemaBuilder {
        const builder = new SchemaBuilder(schema.name, schema.description);

        Object.entries(schema.properties).forEach(([propName, propConfig]) => {
            if (propConfig.type === 'array') {
                builder.addArrayProperty(
                    propName,
                    propConfig.description,
                    propConfig.required,
                    propConfig.enum
                );
            } else {
                builder.addStringProperty(
                    propName,
                    propConfig.description,
                    propConfig.required,
                    propConfig.enum
                );
            }

            // Add relationship if defined
            if (propConfig.relationship) {
                builder.addRelationship(
                    propName,
                    propConfig.relationship.edgeType,
                    propConfig.relationship.description,
                    propConfig.relationship.nodeType
                );
            }
        });

        if (schema.additionalProperties !== undefined) {
            builder.allowAdditionalProperties(schema.additionalProperties);
        }

        return builder;
    }

    /**
     * Loads all schema files from the schemas directory.
     */
    static async loadAllSchemas(): Promise<Record<string, SchemaBuilder>> {
        const SCHEMAS_DIR = CONFIG.PATHS.SCHEMAS_DIR;

        try {
            const files = await fs.readdir(SCHEMAS_DIR);
            const schemaFiles = files.filter(file => file.endsWith('.schema.json'));

            const schemas: Record<string, SchemaBuilder> = {};
            for (const file of schemaFiles) {
                const schemaName = path.basename(file, '.schema.json');
                schemas[schemaName] = await this.loadSchema(schemaName);
            }

            return schemas;
        } catch (error) {
            if (error instanceof Error) {
                throw new Error(`Failed to load schemas: ${error.message}`);
            }
            throw new Error('Failed to load schemas');
        }
    }

    /**
     * Validates a schema definition.
     * @throws {Error} If the schema is invalid
     */
    private static validateSchema(schema: RawSchema): void {
        if (!schema.name || !schema.description || !schema.properties) {
            throw new Error('Schema must have name, description, and properties');
        }

        Object.entries(schema.properties).forEach(([propName, propConfig]) => {
            if (!propConfig.type || !propConfig.description) {
                throw new Error(`Property ${propName} must have type and description`);
            }

            if (propConfig.relationship && !propConfig.relationship.edgeType) {
                throw new Error(`Relationship property ${propName} must have edgeType`);
            }
        });
    }
}