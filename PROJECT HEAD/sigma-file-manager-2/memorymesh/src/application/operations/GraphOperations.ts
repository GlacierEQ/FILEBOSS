// src/core/operations/GraphOperations.ts

import {EventEmitter} from '@infrastructure/index.js';
import type {
    INodeManager,
    IEdgeManager,
    IMetadataManager
} from '@application/index.js';
import type {
    Node,
    Edge,
    MetadataAddition,
    MetadataDeletion,
    MetadataResult
} from '@core/index.js';
import type {
    EdgeFilter,
    GetEdgesResult
} from '@shared/index.js';

export class GraphOperations extends EventEmitter {
    constructor(
        private nodeManager: INodeManager,
        private edgeManager: IEdgeManager,
        private metadataManager: IMetadataManager
    ) {
        super();
    }

    async addNodes(nodes: Node[]): Promise<Node[]> {
        this.emit('beforeAddNodes', {nodes});
        const result = await this.nodeManager.addNodes(nodes);
        this.emit('afterAddNodes', {nodes: result});
        return result;
    }

    async updateNodes(nodes: Partial<Node>[]): Promise<Node[]> {
        this.emit('beforeUpdateNodes', {nodes});
        const result = await this.nodeManager.updateNodes(nodes);
        this.emit('afterUpdateNodes', {nodes: result});
        return result;
    }

    async deleteNodes(nodeNames: string[]): Promise<void> {
        this.emit('beforeDeleteNodes', {nodeNames});
        await this.nodeManager.deleteNodes(nodeNames);
        this.emit('afterDeleteNodes', {nodeNames});
    }

    async addEdges(edges: Edge[]): Promise<Edge[]> {
        this.emit('beforeAddEdges', {edges});
        const result = await this.edgeManager.addEdges(edges);
        this.emit('afterAddEdges', {edges: result});
        return result;
    }

    async updateEdges(edges: Edge[]): Promise<Edge[]> {
        this.emit('beforeUpdateEdges', {edges});
        const result = await this.edgeManager.updateEdges(edges);
        this.emit('afterUpdateEdges', {edges: result});
        return result;
    }

    async deleteEdges(edges: Edge[]): Promise<void> {
        this.emit('beforeDeleteEdges', {edges});
        await this.edgeManager.deleteEdges(edges);
        this.emit('afterDeleteEdges', {edges});
    }

    async getEdges(filter?: EdgeFilter): Promise<GetEdgesResult> {
        const edges = await this.edgeManager.getEdges(filter);
        return {edges};
    }

    async addMetadata(metadata: MetadataAddition[]): Promise<MetadataResult[]> {
        this.emit('beforeAddMetadata', {metadata});
        const result = await this.metadataManager.addMetadata(metadata);
        this.emit('afterAddMetadata', {results: result});
        return result;
    }

    async deleteMetadata(deletions: MetadataDeletion[]): Promise<void> {
        this.emit('beforeDeleteMetadata', {deletions});
        await this.metadataManager.deleteMetadata(deletions);
        this.emit('afterDeleteMetadata', {deletions});
    }
}