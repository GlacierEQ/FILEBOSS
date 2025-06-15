// src/core/operations/TransactionOperations.ts

import {EventEmitter} from '@infrastructure/index.js';
import type {ITransactionManager} from '@application/index.js';
import type {Graph} from '@core/index.js';

export class TransactionOperations extends EventEmitter {
    constructor(private transactionManager: ITransactionManager) {
        super();
    }

    async beginTransaction(): Promise<void> {
        this.emit('beforeBeginTransaction', {});
        await this.transactionManager.beginTransaction();
        this.emit('afterBeginTransaction', {});
    }

    async commit(): Promise<void> {
        this.emit('beforeCommit', {});
        await this.transactionManager.commit();
        this.emit('afterCommit', {});
    }

    async rollback(): Promise<void> {
        this.emit('beforeRollback', {});
        await this.transactionManager.rollback();
        this.emit('afterRollback', {});
    }

    async withTransaction<T>(operation: () => Promise<T>): Promise<T> {
        await this.beginTransaction();
        try {
            const result = await operation();
            await this.commit();
            return result;
        } catch (error) {
            await this.rollback();
            throw error;
        }
    }

    async addRollbackAction(action: () => Promise<void>, description: string): Promise<void> {
        await this.transactionManager.addRollbackAction(action, description);
    }

    isInTransaction(): boolean {
        return this.transactionManager.isInTransaction();
    }

    getCurrentGraph(): Graph {
        return this.transactionManager.getCurrentGraph();
    }
}