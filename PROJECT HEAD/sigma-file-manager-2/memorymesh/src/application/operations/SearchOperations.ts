// src/core/operations/SearchOperations.ts

import {EventEmitter} from '@infrastructure/index.js';
import type {ISearchManager} from '@application/index.js';
import type {OpenNodesResult} from '@shared/index.js';
import type {Graph} from '@core/index.js';

export class SearchOperations extends EventEmitter {
    constructor(private searchManager: ISearchManager) {
        super();
    }

    async searchNodes(query: string): Promise<OpenNodesResult> {
        this.emit('beforeSearch', {query});
        const result = await this.searchManager.searchNodes(query);
        this.emit('afterSearch', result);
        return result;
    }

    async openNodes(names: string[]): Promise<OpenNodesResult> {
        this.emit('beforeOpenNodes', {names});
        const result = await this.searchManager.openNodes(names);
        this.emit('afterOpenNodes', result);
        return result;
    }

    async readGraph(): Promise<Graph> {
        this.emit('beforeReadGraph', {});
        const result = await this.searchManager.readGraph();
        this.emit('afterReadGraph', result);
        return result;
    }
}