// src/core/events/EventEmitter.ts

import type {EventListener} from './EventTypes.ts';

/**
 * A simple event emitter implementation for managing event listeners and emitting events.
 */
export class EventEmitter {
    /**
     * Maps event names to their respective sets of listener functions.
     */
    private eventListeners: Map<string, Set<EventListener>>;

    constructor() {
        this.eventListeners = new Map();

        // Bind methods to ensure correct 'this' context
        this.on = this.on.bind(this);
        this.off = this.off.bind(this);
        this.once = this.once.bind(this);
        this.emit = this.emit.bind(this);
        this.removeAllListeners = this.removeAllListeners.bind(this);
    }

    /**
     * Adds an event listener for the specified event.
     */
    public on(eventName: string, listener: EventListener): () => void {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function');
        }

        if (!this.eventListeners.has(eventName)) {
            this.eventListeners.set(eventName, new Set());
        }

        const listeners = this.eventListeners.get(eventName);
        if (listeners) {
            listeners.add(listener);
        }

        // Return unsubscribe function
        return () => this.off(eventName, listener);
    }

    /**
     * Removes an event listener for the specified event.
     */
    public off(eventName: string, listener: EventListener): void {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function');
        }

        const listeners = this.eventListeners.get(eventName);
        if (listeners) {
            listeners.delete(listener);

            // Clean up empty listener sets
            if (listeners.size === 0) {
                this.eventListeners.delete(eventName);
            }
        }
    }

    /**
     * Adds a one-time event listener that removes itself after being called.
     */
    public once(eventName: string, listener: EventListener): () => void {
        if (typeof listener !== 'function') {
            throw new TypeError('Listener must be a function');
        }

        const onceWrapper: EventListener = (data: any) => {
            this.off(eventName, onceWrapper);
            listener(data);
        };

        return this.on(eventName, onceWrapper);
    }

    /**
     * Emits an event with the specified data to all registered listeners.
     */
    public emit(eventName: string, data?: any): boolean {

        const listeners = this.eventListeners.get(eventName);
        if (!listeners) {
            return false;
        }

        const errors: Error[] = [];
        listeners.forEach(listener => {
            try {
                listener(data);
            } catch (error) {
                errors.push(error instanceof Error ? error : new Error(String(error)));
            }
        });

        if (errors.length > 0) {
            throw new Error(`Multiple errors occurred while emitting "${eventName}" event: ${errors.map(e => e.message).join(', ')}`);
        }

        return true;
    }

    /**
     * Removes all listeners for a specific event or all events.
     */
    public removeAllListeners(eventName?: string): void {
        if (eventName === undefined) {
            this.eventListeners.clear();
        } else {
            this.eventListeners.delete(eventName);
        }
    }

    /**
     * Gets the number of listeners for a specific event.
     */
    public listenerCount(eventName: string): number {

        const listeners = this.eventListeners.get(eventName);
        return listeners ? listeners.size : 0;
    }

    /**
     * Gets all registered event names.
     */
    public eventNames(): string[] {
        return Array.from(this.eventListeners.keys());
    }

    /**
     * Gets all listeners for a specific event.
     */
    public getListeners(eventName: string): EventListener[] {

        const listeners = this.eventListeners.get(eventName);
        return listeners ? Array.from(listeners) : [];
    }
}