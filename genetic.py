"""Genetic Algorithm implementation for tournament scheduling.

This module implements a GA with configurable selection and crossover
operators so it can be used with different GA configurations for
comparative experiments.
"""

from __future__ import annotations
from typing import List, Tuple
import random
from utils import (
    Match,
    Schedule,
    GAParameters,
    random_individual,
    schedule_rounds_from_order,
)

Individual = List[Match]


# ---------------- Fitness ---------------- #

def fitness(num_teams: int, indiv: Individual) -> float:
    """
    Higher is better.
    Criteria:
    - Fewer rounds is better.
    - Penalize long gaps and back-to-back matches for the same team.
    """
    schedule = schedule_rounds_from_order(num_teams, indiv)
    num_rounds = len(schedule)
    score = -num_rounds  # prefer fewer rounds

    team_rounds = {t: [] for t in range(num_teams)}
    for r_idx, rnd in enumerate(schedule):
        for h, a in rnd:
            team_rounds[h].append(r_idx)
            team_rounds[a].append(r_idx)

    for t in range(num_teams):
        rounds = sorted(team_rounds[t])
        if not rounds:
            score -= 5
            continue
        for i in range(1, len(rounds)):
            gap = rounds[i] - rounds[i - 1]
            if gap == 0:
                score -= 10          # impossible clash
            elif gap == 1:
                score -= 0.5         # back-to-back rounds
            elif gap > 3:
                score -= (gap - 3) * 0.5  # long idle gaps

    return score


# ---------------- Selection ---------------- #

def tournament_selection(population: List[Individual],
                         fit_values: List[float],
                         k: int) -> Individual:
    """Standard tournament selection."""
    indices = random.sample(range(len(population)), k)
    best_i = max(indices, key=lambda i: fit_values[i])
    return population[best_i][:]


def roulette_selection(population: List[Individual],
                       fit_values: List[float]) -> Individual:
    """
    Roulette wheel (fitness-proportionate) selection.
    """
    min_fit = min(fit_values)
    shifted = [f - min_fit + 1e-6 for f in fit_values]  # avoid negatives/zeros
    total = sum(shifted)
    r = random.uniform(0, total)
    acc = 0.0
    for indiv, f in zip(population, shifted):
        acc += f
        if acc >= r:
            return indiv[:]
    return population[-1][:]


# ---------------- Crossover & Mutation ---------------- #

def one_point_crossover(p1: Individual, p2: Individual) -> Tuple[Individual, Individual]:
    """One-point crossover adapted to permutations."""
    size = len(p1)
    if size < 2:
        return p1[:], p2[:]
    cx_point = random.randint(1, size - 1)

    def make_child(a, b):
        head = a[:cx_point]
        tail = [m for m in b if m not in head]
        return head + tail

    return make_child(p1, p2), make_child(p2, p1)


def two_point_crossover(p1: Individual, p2: Individual) -> Tuple[Individual, Individual]:
    """Two-point crossover similar to standard GA diagrams."""
    size = len(p1)
    if size < 2:
        return p1[:], p2[:]
    i, j = sorted(random.sample(range(size), 2))

    def make_child(a, b):
        mid = a[i:j]
        rest = [m for m in b if m not in mid]
        return rest[:i] + mid + rest[i:]

    return make_child(p1, p2), make_child(p2, p1)


def mutate(indiv: Individual, mutation_rate: float) -> None:
    """Swap mutation: randomly swap two genes with given probability."""
    n = len(indiv)
    if n < 2:
        return
    for _ in range(n):
        if random.random() < mutation_rate:
            i, j = random.sample(range(n), 2)
            indiv[i], indiv[j] = indiv[j], indiv[i]


# ---------------- Main GA ---------------- #

def genetic_algorithm_schedule(num_teams: int,
                               params: GAParameters) -> Tuple[Schedule, float, List[float]]:
    """
    Run genetic algorithm and return best schedule and its fitness.
    """
    # Initial population
    population: List[Individual] = [
        random_individual(num_teams) for _ in range(params.population_size)
    ]

    best_indiv = None
    best_fit = float("-inf")

    fitness_history: List[float] = []
    for _ in range(params.generations):
        fit_values = [fitness(num_teams, ind) for ind in population]

        # Track global best
        gen_best_i = max(range(len(population)), key=lambda i: fit_values[i])
        if fit_values[gen_best_i] > best_fit:
            best_fit = fit_values[gen_best_i]
            best_indiv = population[gen_best_i][:]

        # record current best for plotting
        fitness_history.append(best_fit)

        new_pop: List[Individual] = []
        if params.elitism and best_indiv is not None:
            new_pop.append(best_indiv[:])

        # Create rest of new population
        while len(new_pop) < params.population_size:
            # Selection according to configured method
            if params.selection_method == "tournament":
                parent1 = tournament_selection(population, fit_values, params.tournament_k)
                parent2 = tournament_selection(population, fit_values, params.tournament_k)
            else:
                parent1 = roulette_selection(population, fit_values)
                parent2 = roulette_selection(population, fit_values)

            if random.random() < params.crossover_rate:
                if params.crossover_operator == "two_point":
                    child1, child2 = two_point_crossover(parent1, parent2)
                else:
                    child1, child2 = one_point_crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]

            mutate(child1, params.mutation_rate)
            mutate(child2, params.mutation_rate)

            new_pop.append(child1)
            if len(new_pop) < params.population_size:
                new_pop.append(child2)

        population = new_pop

    best_schedule = schedule_rounds_from_order(num_teams, best_indiv)
    return best_schedule, best_fit, fitness_history
