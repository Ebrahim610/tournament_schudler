Project 12 - Tournament Scheduling (Phase 2 Implementation)

This workspace contains a simple implementation of a Genetic Algorithm (GA)
for tournament scheduling, a greedy heuristic baseline, and a small Tkinter GUI
for running experiments and comparisons.

Quick start

1. (Optional) Create and activate a virtual environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Run the GUI:

  PowerShell (recommended):

  ```powershell
  # create and activate venv (first time)
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt

  # run GUI
  python src/src/main.py
  ```

  Or from an already activated environment:

  ```powershell
  python src/src/main.py
  ```

4. Run experiments (batch):

  ```powershell
  # from repository root
  python src/experiments/run_experiments.py
  ```

Files of interest

- `src/baselines.py`: Baseline implementations (random + greedy heuristic).
- `src/genetic.py`: Genetic Algorithm implementation (configurable).
- `src/gui.py`: Tkinter GUI to run experiments and compare methods.
- `src/utils.py`: Helper functions and data types.

## Pseudocode

### Genetic Algorithm Main Loop

```
Algorithm: Genetic Algorithm for Tournament Scheduling

Input:
  - num_teams: number of teams (integer)
  - params: GA parameters (population_size, generations, mutation_rate, crossover_rate, etc.)

Output:
  - best_schedule: the best feasible tournament schedule found

Procedure:
  1. Generate initial population of random individuals
     FOR i = 1 TO population_size DO
       individual[i] = random permutation of all pairings
     END FOR

  2. FOR generation = 1 TO num_generations DO
       
       3. Evaluate fitness of all individuals
          FOR each individual IN population DO
            fitness[individual] = compute_fitness(individual, num_teams)
          END FOR

       4. Track the best individual (for elitism)
          best_individual = individual with highest fitness
          best_fitness = fitness of best_individual

       5. Create new population
          new_population = empty list
          
          IF elitism enabled THEN
            Add best_individual to new_population
          END IF

          WHILE len(new_population) < population_size DO
            
            6. Select two parents using selection method
               parent1 = select_parent(population, fitness, selection_method)
               parent2 = select_parent(population, fitness, selection_method)

            7. Apply crossover with probability crossover_rate
               IF random() < crossover_rate THEN
                 (child1, child2) = crossover(parent1, parent2)
               ELSE
                 child1 = copy(parent1)
                 child2 = copy(parent2)
               END IF

            8. Apply mutation with probability mutation_rate
               mutate(child1, mutation_rate)
               mutate(child2, mutation_rate)

            9. Add children to new population
               ADD child1 to new_population
               IF len(new_population) < population_size THEN
                 ADD child2 to new_population
               END IF

          END WHILE

          population = new_population

       END FOR generation

  10. Convert best individual (permutation) to schedule and return
      best_schedule = convert_permutation_to_schedule(best_individual, num_teams)
      RETURN best_schedule

End Algorithm
```

### Greedy Baseline

```
Algorithm: Greedy Tournament Scheduling

Input:
  - num_teams: number of teams (integer)

Output:
  - schedule: list of rounds, where each round is a list of matches

Procedure:
  1. Generate all possible pairings
     all_pairings = [pair (i, j) for all i < j in range(num_teams)]

  2. Initialize
     remaining_pairings = copy(all_pairings)
     schedule = empty list
     current_round = empty list
     used_teams = empty set

  3. Build rounds greedily
     WHILE remaining_pairings is not empty DO
       
       current_round = empty list
       used_teams = empty set

       FOR each pairing (team_a, team_b) IN remaining_pairings DO
         
         IF team_a NOT IN used_teams AND team_b NOT IN used_teams THEN
           ADD (team_a, team_b) to current_round
           ADD team_a to used_teams
           ADD team_b to used_teams
           REMOVE (team_a, team_b) from remaining_pairings
         
         END IF

       END FOR

       ADD current_round to schedule

     END WHILE

  4. RETURN schedule

End Algorithm
```

### Fitness Function

```
Algorithm: Compute Fitness of a Schedule

Input:
  - num_teams: number of teams (integer)
  - individual: permutation of pairings (chromosome)

Output:
  - fitness: numeric score (higher is better)

Procedure:
  1. Convert permutation to schedule
     schedule = convert_permutation_to_rounds(individual, num_teams)

  2. Initialize fitness
     fitness = 0
     num_rounds = length(schedule)

  3. Primary objective: minimize number of rounds
     fitness = -num_rounds  (negative because we want to minimize)

  4. For each team, track which rounds it plays
     team_rounds[t] = empty list for each team t in range(num_teams)
     
     FOR each round_index, round IN enumerate(schedule) DO
       FOR each match (home, away) IN round DO
         ADD round_index to team_rounds[home]
         ADD round_index to team_rounds[away]
       END FOR
     END FOR

  5. Secondary objective: penalize long gaps and back-to-back matches
     FOR each team t in range(num_teams) DO
       
       rounds = sorted list of round indices where team t plays
       
       IF rounds is empty THEN
         fitness -= 5  (team doesn't play: bad)
       ELSE
         FOR i = 1 TO len(rounds) - 1 DO
           gap = rounds[i] - rounds[i-1]
           
           IF gap == 1 THEN
             fitness -= 0.5  (back-to-back: slightly bad)
           ELSE IF gap > 3 THEN
             fitness -= (gap - 3) * 0.5  (long idle: penalize)
           END IF
         
         END FOR
       
       END FOR

     END FOR

  6. RETURN fitness

End Algorithm
```

### Random Baseline

```
Algorithm: Random Tournament Scheduling

Input:
  - num_teams: number of teams (integer)

Output:
  - schedule: list of rounds

Procedure:
  1. Generate all possible pairings
     all_pairings = [pair (i, j) for all i < j in range(num_teams)]

  2. Shuffle pairings randomly
     shuffled_pairings = random_shuffle(all_pairings)

  3. Pack into rounds greedily
     schedule = convert_pairings_to_rounds(shuffled_pairings, num_teams)

  4. RETURN schedule

End Algorithm
```

---

## Key Concepts Explained

**Chromosome:** A permutation of all possible team pairings (matches). For 4 teams, there are 6 pairings, so the chromosome is a list of these 6 matches in some order.

**Fitness:** A numeric score that evaluates how good a schedule is. Higher fitness = better schedule. We minimize rounds and penalize gaps/conflicts.

**Selection:** Choosing two parents from the population based on their fitness (better individuals more likely to reproduce).

**Crossover:** Combining two parent permutations to create offspring, preserving partial order of matches.

**Mutation:** Randomly swapping two matches in a permutation to introduce variation.

**Elitism:** Keeping the best individual(s) unchanged into the next generation to avoid losing good solutions.

Notes

- This repository supplies three GA presets accessible from the GUI for
  comparative experiments (Default, Large Population, High Mutation).
- Replace `UserManual.pdf` with a proper user manual PDF before submission.
