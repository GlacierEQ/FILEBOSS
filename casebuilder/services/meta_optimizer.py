"""Simple evolutionary optimizer for demonstration purposes."""

from __future__ import annotations

import random
from typing import Callable, Tuple


class EvolutionaryOptimizer:
    """Optimize a single variable using a basic evolutionary strategy."""

    def __init__(self, population_size: int = 20, generations: int = 50, mutation_rate: float = 0.1) -> None:
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    def optimize(self, fitness_fn: Callable[[float], float], domain: Tuple[float, float]) -> float:
        """Return the best value found within ``domain``."""
        low, high = domain
        population = [random.uniform(low, high) for _ in range(self.population_size)]
        best = population[0]
        best_score = fitness_fn(best)
        for _ in range(self.generations):
            scores = [fitness_fn(ind) for ind in population]
            best_idx = scores.index(max(scores))
            if scores[best_idx] > best_score:
                best_score = scores[best_idx]
                best = population[best_idx]
            selected = [x for _, x in sorted(zip(scores, population), reverse=True)][: self.population_size // 2]
            children = []
            while len(children) + len(selected) < self.population_size:
                a, b = random.sample(selected, 2)
                child = (a + b) / 2
                if random.random() < self.mutation_rate:
                    child += random.uniform(-1.0, 1.0)
                child = max(low, min(high, child))
                children.append(child)
            population = selected + children
        return best
