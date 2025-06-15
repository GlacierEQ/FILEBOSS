// src/schema/loader/schemaBuilder.ts

/**
 * Schema property configuration
 */
export interface SchemaPropertyConfig {
    type: string;
    description: string;
    enum?: string[];
    items?: Partial<SchemaPropertyConfig>;
    properties?: Record<string, SchemaPropertyConfig>;
    required?: string[];
}

/**
 * Relationship configuration
 */
export interface RelationshipConfig {
    edgeType: string;
    nodeType?: string;
    description?: string;
}

/**
 * Metadata configuration
 */
export interface MetadataConfig {
    requiredFields: string[];
    optionalFields: string[];
    excludeFields: string[];
}

/**
 * Schema configuration
 */
export interface SchemaConfig {
    name: string;
    description: string;
    inputSchema: {
        type: string;
        properties: Record<string, {
            type: string;
            properties: Record<string, SchemaPropertyConfig>;
            required: string[];
            additionalProperties: boolean | SchemaPropertyConfig;
        }>;
        required: string[];
    };
    relationships: Record<string, RelationshipConfig>;
    metadataConfig: MetadataConfig;
}

/**
 * Facilitates the construction and manipulation of schemas for nodes in the knowledge graph.
 */
export class SchemaBuilder {
    private schema: Partial<SchemaConfig>;
    private relationships: Map<string, RelationshipConfig>;
    private metadataConfig: MetadataConfig;

    /**
     * Creates an instance of SchemaBuilder.
     */
    constructor(name: string, description: string) {
        this.schema = {
            name,
            description,
            inputSchema: {
                type: "object",
                properties: {
                    [name.replace('add_', '')]: {
                        type: "object",
                        properties: {},
                        required: [],
                        additionalProperties: {
                            type: "string",
                            description: "Any additional properties"
                        }
                    }
                },
                required: [name.replace('add_', '')]
            }
        };

        this.relationships = new Map();
        this.metadataConfig = {
            requiredFields: [],
            optionalFields: [],
            excludeFields: []
        };
    }

    /**
     * Adds a string property to the schema with an optional enum.
     */
    addStringProperty(
        name: string,
        description: string,
        required: boolean = false,
        enumValues: string[] | null = null
    ): SchemaBuilder {
        const property: SchemaPropertyConfig = {
            type: "string",
            description
        };

        if (enumValues) {
            property.enum = enumValues;
        }

        const schemaName = this.schema.name!.replace('add_', '');
        if (this.schema.inputSchema?.properties[schemaName]) {
            this.schema.inputSchema.properties[schemaName].properties[name] = property;

            if (required) {
                this.schema.inputSchema.properties[schemaName].required.push(name);
                this.metadataConfig.requiredFields.push(name);
            } else {
                this.metadataConfig.optionalFields.push(name);
            }
        }

        return this;
    }

    /**
     * Adds an array property to the schema with optional enum values for items.
     */
    addArrayProperty(
        name: string,
        description: string,
        required: boolean = false,
        enumValues: string[] | null = null
    ): SchemaBuilder {
        const property: SchemaPropertyConfig = {
            type: "array",
            description,
            items: {
                type: "string",
                description: `Item in ${name} array`,
                ...(enumValues && {enum: enumValues})
            }
        };

        const schemaName = this.schema.name!.replace('add_', '');
        if (this.schema.inputSchema?.properties[schemaName]) {
            this.schema.inputSchema.properties[schemaName].properties[name] = property;

            if (required) {
                this.schema.inputSchema.properties[schemaName].required.push(name);
                this.metadataConfig.requiredFields.push(name);
            } else {
                this.metadataConfig.optionalFields.push(name);
            }
        }

        return this;
    }

    /**
     * Adds a relationship definition to the schema.
     */
    addRelationship(
        propertyName: string,
        edgeType: string,
        description: string,
        nodeType: string | null = null
    ): SchemaBuilder {
        this.relationships.set(propertyName, {
            edgeType,
            ...(nodeType && {nodeType}),
            description
        });
        this.metadataConfig.excludeFields.push(propertyName);
        return this.addArrayProperty(propertyName, description);
    }

    /**
     * Sets whether additional properties are allowed in the schema.
     */
    allowAdditionalProperties(allowed: boolean): SchemaBuilder {
        const schemaName = this.schema.name!.replace('add_', '');
        if (this.schema.inputSchema?.properties[schemaName]) {
            if (allowed) {
                this.schema.inputSchema.properties[schemaName].additionalProperties = {
                    type: "string",
                    description: "Additional property value"
                };
            } else {
                this.schema.inputSchema.properties[schemaName].additionalProperties = false;
            }
        }
        return this;
    }

    /**
     * Creates an update schema based on the current schema.
     */
    createUpdateSchema(excludeFields: Set<string> = new Set()): SchemaConfig {
        const schemaName = this.schema.name!.replace('add_', 'update_');
        const updateSchemaBuilder = new SchemaBuilder(
            schemaName,
            `Update an existing ${schemaName.replace('update_', '')} in the knowledge graph`
        );

        const baseProperties = this.schema.inputSchema!.properties[this.schema.name!.replace('add_', '')].properties;

        // Copy properties except excluded ones
        Object.entries(baseProperties).forEach(([propName, propValue]) => {
            if (!excludeFields.has(propName)) {
                if (propValue.type === 'array') {
                    updateSchemaBuilder.addArrayProperty(
                        propName,
                        propValue.description,
                        false,
                        propValue.items?.enum
                    );
                } else {
                    updateSchemaBuilder.addStringProperty(
                        propName,
                        propValue.description,
                        false,
                        propValue.enum
                    );
                }
            }
        });

        // Copy relationships
        this.relationships.forEach((config, propName) => {
            if (!excludeFields.has(propName)) {
                updateSchemaBuilder.addRelationship(
                    propName,
                    config.edgeType,
                    config.description || 'Relationship property',
                    config.nodeType || null
                );
            }
        });

        // Add metadata array
        updateSchemaBuilder.addArrayProperty(
            'metadata',
            'An array of metadata contents to replace the existing metadata'
        );

        return updateSchemaBuilder.build();
    }

    /**
     * Builds and returns the final schema object.
     */
    build(): SchemaConfig {
        return {
            ...this.schema as SchemaConfig,
            relationships: Object.fromEntries(this.relationships),
            metadataConfig: this.metadataConfig
        };
    }
}