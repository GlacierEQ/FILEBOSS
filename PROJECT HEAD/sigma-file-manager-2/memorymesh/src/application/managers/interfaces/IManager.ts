// src/application/managers/interfaces/IManager.ts

import {EventEmitter, IStorage} from '@infrastructure/index.js';

/**
 * Abstract base class for all manager interfaces.
 * Provides event emission capabilities and implements common initialization.
 */
export abstract class IManager extends EventEmitter {
    /**
     * The storage instance used by the manager.
     */
    protected storage: IStorage;

    /**
     * Creates an instance of IManager.
     * @param storage - The storage mechanism to use for persisting the knowledge graph.
     * @throws {Error} If attempting to instantiate the abstract class directly.
     */
    constructor(storage: IStorage) {
        super();
        if (new.target === IManager) {
            throw new Error('IManager is an abstract class');
        }
        this.storage = storage;
    }

    /**
     * Initializes the manager by emitting the 'initialized' event.
     * Common implementation for all manager classes.
     */
    public async initialize(): Promise<void> {
        this.emit('initialized', {manager: this.constructor.name});
    }
}