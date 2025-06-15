// src/core/schema/index.ts

export { SchemaBuilder } from './SchemaBuilder.js';
export { SchemaLoader } from './SchemaLoader.js';
export {
    createSchemaNode,
    updateSchemaNode,
    handleSchemaUpdate,
    handleSchemaDelete
} from './SchemaProcessor.js';

export type {
    SchemaPropertyConfig,
    RelationshipConfig,
    MetadataConfig,
    SchemaConfig
} from './SchemaBuilder.js';

export type {
    ProcessedNodeResult,
    SchemaUpdateResult
} from './SchemaProcessor.js';