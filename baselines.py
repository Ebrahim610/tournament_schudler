"""Baseline scheduling algorithms and simple heuristics.

This module provides a random baseline and a simple greedy baseline
which will be useful as a comparison to the Genetic Algorithm.
"""

from typing import List
from utils import (
    Schedule,
    random_individual,
    schedule_rounds_from_order,
    generate_all_pairings,
)


def baseline_random_schedule(num_teams: int) -> Schedule:
    """Return a random feasible schedule (random permutation of pairings)."""
    indiv = random_individual(num_teams)
    return schedule_rounds_from_order(num_teams, indiv)


def greedy_schedule(num_teams: int) -> Schedule:
    """Greedy heuristic: repeatedly form rounds by picking any available pairing
    that doesn't conflict with the current round until all pairings are scheduled.
    This tends to produce reasonable (but not optimal) round counts quickly.
    """
    pairings = generate_all_pairings(num_teams)
    remaining = pairings[:]
    rounds: Schedule = []

    while remaining:
        used = set()
        current_round = []
        for m in remaining[:]:
            a, b = m
            if a not in used and b not in used:
                current_round.append(m)
                used.add(a)
                used.add(b)
                remaining.remove(m)
        rounds.append(current_round)

    return rounds
