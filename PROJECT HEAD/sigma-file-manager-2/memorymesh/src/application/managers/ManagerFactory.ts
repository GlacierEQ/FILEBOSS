// src/core/managers/ManagerFactory.ts

import {
    NodeManager,
    EdgeManager,
    MetadataManager,
    SearchManager,
    TransactionManager
} from '@application/index.js';
import type {IStorage} from '@infrastructure/index.js';
import type {
    INodeManager,
    IEdgeManager,
    IMetadataManager,
    ISearchManager,
    ITransactionManager
} from '@application/index.js';

/**
 * Factory class responsible for creating instances of various manager classes
 * used in the knowledge graph. Ensures consistent initialization and configuration
 * of all manager instances.
 */
export class ManagerFactory {
    private static instances: {
        nodeManager?: NodeManager;
        edgeManager?: EdgeManager;
        metadataManager?: MetadataManager;
        searchManager?: SearchManager;
        transactionManager?: TransactionManager;
    } = {};

    /**
     * Creates or returns an existing instance of NodeManager
     */
    static getNodeManager(storage: IStorage): INodeManager {
        if (!this.instances.nodeManager) {
            this.instances.nodeManager = new NodeManager(storage);
        }
        return this.instances.nodeManager;
    }

    /**
     * Creates or returns an existing instance of EdgeManager
     */
    static getEdgeManager(storage: IStorage): IEdgeManager {
        if (!this.instances.edgeManager) {
            this.instances.edgeManager = new EdgeManager(storage);
        }
        return this.instances.edgeManager;
    }

    /**
     * Creates or returns an existing instance of MetadataManager
     */
    static getMetadataManager(storage: IStorage): IMetadataManager {
        if (!this.instances.metadataManager) {
            this.instances.metadataManager = new MetadataManager(storage);
        }
        return this.instances.metadataManager;
    }

    /**
     * Creates or returns an existing instance of SearchManager
     */
    static getSearchManager(storage: IStorage): ISearchManager {
        if (!this.instances.searchManager) {
            this.instances.searchManager = new SearchManager(storage);
        }
        return this.instances.searchManager;
    }

    /**
     * Creates or returns an existing instance of TransactionManager
     */
    static getTransactionManager(storage: IStorage): ITransactionManager {
        if (!this.instances.transactionManager) {
            this.instances.transactionManager = new TransactionManager(storage);
        }
        return this.instances.transactionManager;
    }

    /**
     * Creates all manager instances at once
     */
    static getAllManagers(storage: IStorage) {
        return {
            nodeManager: this.getNodeManager(storage),
            edgeManager: this.getEdgeManager(storage),
            metadataManager: this.getMetadataManager(storage),
            searchManager: this.getSearchManager(storage),
            transactionManager: this.getTransactionManager(storage)
        };
    }

    /**
     * Clears all cached manager instances
     */
    static clearInstances(): void {
        this.instances = {};
    }
}