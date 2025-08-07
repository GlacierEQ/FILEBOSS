from casebuilder.services.meta_optimizer import EvolutionaryOptimizer


def test_evolutionary_optimizer_simple():
    def fitness(x: float) -> float:
        return -((x - 5) ** 2)

    optimizer = EvolutionaryOptimizer(population_size=30, generations=20)
    best = optimizer.optimize(fitness, (0, 10))
    assert abs(best - 5) < 1
