// src/core/managers/implementations/TransactionManager.ts

import {ITransactionManager, RollbackAction} from './interfaces/ITransactionManager.js';
import { IManager } from './interfaces/IManager.js';
import type {Graph} from '@core/index.js';
import type {IStorage} from '@infrastructure/index.js';

/**
 * Implements transaction-related operations for the knowledge graph.
 * Handles transaction lifecycle, rollback actions, and maintaining transaction state.
 */
export class TransactionManager extends IManager implements ITransactionManager {
    private graph: Graph;
    private rollbackActions: RollbackAction[];
    private inTransaction: boolean;

    constructor(storage: IStorage) {
        super(storage);
        this.graph = {nodes: [], edges: []};
        this.rollbackActions = [];
        this.inTransaction = false;
    }

    /**
     * Begins a new transaction.
     * @throws Error if a transaction is already in progress
     */
    async beginTransaction(): Promise<void> {
        if (this.inTransaction) {
            throw new Error('Transaction already in progress');
        }

        this.emit('beforeBeginTransaction', {});

        try {
            // Load current state
            this.graph = await this.storage.loadGraph();
            this.rollbackActions = [];
            this.inTransaction = true;

            this.emit('afterBeginTransaction', {});
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to begin transaction: ${message}`);
        }
    }

    /**
     * Adds a rollback action to be executed if the transaction is rolled back.
     * @throws Error if no transaction is in progress
     */
    async addRollbackAction(action: () => Promise<void>, description: string): Promise<void> {
        if (!this.inTransaction) {
            throw new Error('No transaction in progress');
        }

        this.rollbackActions.push({action, description});
    }

    /**
     * Commits the current transaction.
     * @throws Error if no transaction is in progress
     */
    async commit(): Promise<void> {
        if (!this.inTransaction) {
            throw new Error('No transaction to commit');
        }

        this.emit('beforeCommit', {});

        try {
            // Clear the transaction state
            this.rollbackActions = [];
            this.inTransaction = false;

            this.emit('afterCommit', {});
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to commit transaction: ${message}`);
        }
    }

    /**
     * Rolls back the current transaction, executing all rollback actions in reverse order.
     * @throws Error if no transaction is in progress
     */
    async rollback(): Promise<void> {
        if (!this.inTransaction) {
            throw new Error('No transaction to rollback');
        }

        this.emit('beforeRollback', {actions: this.rollbackActions});

        try {
            // Execute rollback actions in reverse order
            for (const {action, description} of this.rollbackActions.reverse()) {
                try {
                    await action();
                } catch (error) {
                    console.error(`Error during rollback action (${description}):`, error);
                    // Continue with other rollbacks even if one fails
                }
            }

            // Clear the transaction state
            this.rollbackActions = [];
            this.inTransaction = false;

            this.emit('afterRollback', {});
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error occurred';
            throw new Error(`Failed to rollback transaction: ${message}`);
        }
    }

    /**
     * Gets the current graph state within the transaction.
     */
    getCurrentGraph(): Graph {
        return this.graph;
    }

    /**
     * Checks if a transaction is currently in progress.
     */
    isInTransaction(): boolean {
        return this.inTransaction;
    }

    /**
     * Executes an operation within a transaction, handling commit and rollback automatically.
     */
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
}