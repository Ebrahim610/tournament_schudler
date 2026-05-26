from dataclasses import dataclass
from typing import List, Tuple
import itertools
import random

Team = int
Match = Tuple[Team, Team]
Round = List[Match]
Schedule = List[Round]


@dataclass
class GAParameters:
    population_size: int = 30
    generations: int = 80
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    tournament_k: int = 3
    selection_method: str = "tournament"  # or 'roulette'
    crossover_operator: str = "one_point"  # or 'two_point'
    elitism: bool = True


def generate_all_pairings(num_teams: int) -> List[Match]:
    """All unique pairings for a single round-robin tournament."""
    return [(i, j) for i, j in itertools.combinations(range(num_teams), 2)]


def schedule_rounds_from_order(num_teams: int, order: List[Match]) -> Schedule:
    """
    Convert an ordered list of pairings into rounds where
    each team appears at most once per round.
    """
    remaining = order[:]
    rounds: Schedule = []

    while remaining:
        used = set()
        current_round: Round = []
        for m in remaining[:]:
            a, b = m
            if a not in used and b not in used:
                current_round.append(m)
                used.add(a)
                used.add(b)
                remaining.remove(m)
        rounds.append(current_round)

    return rounds


def random_individual(num_teams: int) -> List[Match]:
    """Random permutation of all pairings = one chromosome."""
    pairings = generate_all_pairings(num_teams)
    random.shuffle(pairings)
    return pairings


def schedule_to_string(schedule: Schedule, team_names: dict | None = None) -> str:
    """Pretty-print a schedule for display in the GUI or export."""
    lines = []
    for r_idx, rnd in enumerate(schedule, start=1):
        lines.append(f"Round {r_idx}:")
        for match in rnd:
            # match can be a 2-tuple (teamA, teamB) or a 3-tuple (teamA, teamB, venue)
            if isinstance(match, (list, tuple)) and len(match) >= 3:
                h, a, venue = match[0], match[1], match[2]
                h_name = team_names.get(h, f"Team {h}") if team_names else f"Team {h}"
                a_name = team_names.get(a, f"Team {a}") if team_names else f"Team {a}"
                lines.append(f"  {h_name} vs {a_name}  @ {venue}")
            elif isinstance(match, (list, tuple)) and len(match) == 2:
                h, a = match
                h_name = team_names.get(h, f"Team {h}") if team_names else f"Team {h}"
                a_name = team_names.get(a, f"Team {a}") if team_names else f"Team {a}"
                lines.append(f"  {h_name} vs {a_name}")
            else:
                # ultimate fallback for weird shapes
                try:
                    h, a = match
                    lines.append(f"  {h} vs {a}")
                except Exception:
                    lines.append(f"  {match}")
        lines.append("")
    return "\n".join(lines).strip()


def add_bye_if_odd(num_teams: int) -> int:
    """Return adjusted number of teams, adding a dummy 'bye' if odd.

    This keeps the scheduling routines simple (even number of teams).
    """
    return num_teams if num_teams % 2 == 0 else num_teams + 1


def pack_into_fixed_rounds(order: List[Match], num_teams: int) -> Schedule:
    """Naive packing of an ordered pairing list into fixed-size rounds.

    This function simply chops the ordering into chunks of size
    `num_teams // 2` to form rounds. It is intentionally naive and may
    produce rounds where a team appears multiple times — useful to show
    'conflicts before solving'.
    """
    chunk = max(1, num_teams // 2)
    rounds: Schedule = []
    for i in range(0, len(order), chunk):
        rounds.append(order[i : i + chunk])
    return rounds


def count_conflicts(schedule: Schedule) -> int:
    """Count conflicts in a schedule.

    A conflict is when a team appears more than once in the same round.
    Returns total number of conflicting occurrences (sum over rounds
    of (count - 1) for teams that appear multiple times).
    """
    conflicts = 0
    for rnd in schedule:
        counts = {}
        for a, b in rnd:
            counts[a] = counts.get(a, 0) + 1
            counts[b] = counts.get(b, 0) + 1
        for c in counts.values():
            if c > 1:
                conflicts += (c - 1)
    return conflicts


def assign_venues(schedule: Schedule, venues: list, strategy: str = "round_robin") -> Schedule:
    """Assign venue names to each match in the schedule for display.

    Returns a new schedule where each match is a tuple of (teamA, teamB, venue_name).
    If `venues` is empty or None, returns the original schedule unchanged.
    Strategies:
    - 'round_robin': pick venues in a rotating pattern across rounds and matches
    - 'random': choose a random venue for each match
    """
    if not venues:
        return schedule

    assigned: Schedule = []
    vcount = len(venues)
    if vcount == 0:
        return schedule

    if strategy == "random":
        for rnd in schedule:
            new_round = []
            for m in rnd:
                venue = random.choice(venues)
                new_round.append((m[0], m[1], venue))
            assigned.append(new_round)
    else:
        # default: round_robin
        for r_idx, rnd in enumerate(schedule):
            new_round = []
            for m_idx, m in enumerate(rnd):
                venue = venues[(r_idx + m_idx) % vcount]
                new_round.append((m[0], m[1], venue))
            assigned.append(new_round)

    return assigned