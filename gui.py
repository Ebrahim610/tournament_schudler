import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
from typing import Optional

# Optional plotting support
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except Exception:
    HAS_MPL = False

from baselines import baseline_random_schedule, greedy_schedule
from genetic import genetic_algorithm_schedule
from utils import (
    schedule_to_string,
    GAParameters,
    add_bye_if_odd,
    random_individual,
    pack_into_fixed_rounds,
    count_conflicts,
    assign_venues,
    schedule_rounds_from_order,
)


class TournamentGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sports Tournament Scheduler with Genetic Algorithm")
        self.geometry("1100x650")
        self.last_results = None
        self.team_names = None  # dict: index -> name
        self.venues = None  # list of venue names
        self._build_layout()

    # ---------------- Layout ---------------- #

    def _build_layout(self):
        # Top frame: parameters + algorithm selection
        top = ttk.Frame(self, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        # Number of teams
        ttk.Label(top, text="Number of teams:").grid(row=0, column=0, sticky="w")
        self.num_teams_var = tk.IntVar(value=8)
        ttk.Entry(top, textvariable=self.num_teams_var, width=8).grid(
            row=0, column=1, padx=5
        )

        # GA parameters
        ttk.Label(top, text="Population:").grid(row=0, column=2, sticky="w")
        self.pop_var = tk.IntVar(value=30)
        ttk.Entry(top, textvariable=self.pop_var, width=8).grid(
            row=0, column=3, padx=5
        )

        ttk.Label(top, text="Generations:").grid(row=0, column=4, sticky="w")
        self.gen_var = tk.IntVar(value=80)
        ttk.Entry(top, textvariable=self.gen_var, width=8).grid(
            row=0, column=5, padx=5
        )

        ttk.Label(top, text="Crossover rate:").grid(row=1, column=0, sticky="w", pady=4)
        self.crossover_var = tk.DoubleVar(value=0.8)
        ttk.Entry(top, textvariable=self.crossover_var, width=8).grid(
            row=1, column=1, padx=5
        )

        ttk.Label(top, text="Mutation rate:").grid(row=1, column=2, sticky="w")
        self.mutation_var = tk.DoubleVar(value=0.1)
        ttk.Entry(top, textvariable=self.mutation_var, width=8).grid(
            row=1, column=3, padx=5
        )

        # Algorithm selection
        ttk.Label(top, text="Algorithm:").grid(row=1, column=4, sticky="w")
        self.algo_var = tk.StringVar(value="Genetic Algorithm")
        algo_combo = ttk.Combobox(
            top,
            textvariable=self.algo_var,
            values=["Baseline (Random)", "Greedy (Heuristic)", "Genetic Algorithm"],
            state="readonly",
            width=22,
        )
        algo_combo.grid(row=1, column=5, padx=5)

        # GA preset selection (three configurations for comparative experiments)
        ttk.Label(top, text="GA Preset:").grid(row=2, column=0, sticky="w", pady=4)
        self.preset_var = tk.StringVar(value="GA Default")
        preset_combo = ttk.Combobox(
            top,
            textvariable=self.preset_var,
            values=["GA Default", "GA Large Population", "GA High Mutation"],
            state="readonly",
            width=22,
        )
        preset_combo.grid(row=2, column=1, padx=5)

        # (Theme selection removed)

        # Buttons
        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=3, column=0, columnspan=6, pady=8, sticky="w")

        ttk.Button(btn_frame, text="Run Selected", command=self.run_selected).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Load Teams", command=self.load_teams).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Load Venues", command=self.load_venues).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Show Distribution", command=self.show_algorithm_distribution).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Open Graph", command=self.open_graph).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Run Both (Compare)", command=self.run_both).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Save Results", command=self.save_results).pack(
            side=tk.LEFT, padx=5
        )

        # Status label
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(
            side=tk.BOTTOM, fill=tk.X
        )

        # Center frame: visualization and results
        center = ttk.Frame(self, padding=10)
        center.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left: process / log (solution process visualization text)
        left = ttk.LabelFrame(center, text="Process / Log", padding=5)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.process_text = tk.Text(left, wrap="word")
        self.process_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll1 = ttk.Scrollbar(left, command=self.process_text.yview)
        scroll1.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_text.configure(yscrollcommand=scroll1.set)

        # Right: results and comparison
        right = ttk.Frame(center)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top-right: selected algorithm result
        sel_frame = ttk.LabelFrame(right, text="Selected Algorithm Result", padding=5)
        sel_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.result_text = tk.Text(sel_frame, wrap="word", height=15)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll2 = ttk.Scrollbar(sel_frame, command=self.result_text.yview)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scroll2.set)

        # Bottom-right: comparison (baseline vs GA)
        cmp_frame = ttk.LabelFrame(right, text="Comparison (Baseline vs GA)", padding=5)
        cmp_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.compare_text = tk.Text(cmp_frame, wrap="word", height=10)
        self.compare_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll3 = ttk.Scrollbar(cmp_frame, command=self.compare_text.yview)
        scroll3.pack(side=tk.RIGHT, fill=tk.Y)
        self.compare_text.configure(yscrollcommand=scroll3.set)

        # Help text for users
        self.process_text.insert(
            "end",
            "Instructions:\n"
            "- Enter number of teams and GA parameters.\n"
            "- Choose an algorithm and click 'Run Selected' to execute.\n"
            "- Use 'GA Preset' to pick one of 3 configurations for comparative tests.\n"
            "- Click 'Run Both' to run Baseline + GA (multiple trials) and compare.\n"
            "- Click 'Save Results' to save the last run to a file.\n",
        )

        # End of UI layout

    # ---------------- Execution / Helpers ---------------- #

    def _build_ga_params_from_ui(self) -> GAParameters:
        params = GAParameters()
        params.population_size = max(4, int(self.pop_var.get()))
        params.generations = max(1, int(self.gen_var.get()))
        params.crossover_rate = float(self.crossover_var.get())
        params.mutation_rate = float(self.mutation_var.get())
        params.tournament_k = max(2, int(params.population_size // 10) or 2)

        # apply preset adjustments
        preset = getattr(self, 'preset_var', tk.StringVar(value='GA Default')).get()
        if preset == "GA Large Population":
            params.population_size = max(params.population_size, 100)
        elif preset == "GA High Mutation":
            params.mutation_rate = max(params.mutation_rate, 0.15)

        # selection and crossover choices
        params.selection_method = "tournament"
        params.crossover_operator = "one_point"
        params.elitism = True
        return params

    def run_selected(self):
        try:
            n = int(self.num_teams_var.get())
        except Exception:
            messagebox.showerror("Input Error", "Please enter a valid number of teams.")
            return

        n_adj = add_bye_if_odd(n)
        if n != n_adj:
            self.process_text.insert("end", f"Odd number of teams detected; adding a bye to make {n_adj} teams.\n")

        choice = self.algo_var.get()
        self.status_var.set("Running...")
        start = time.time()

        if choice == "Baseline (Random)":
            # before: naive packing of a random ordering
            naive = random_individual(n_adj)
            before_sched = pack_into_fixed_rounds(naive, n_adj)
            conflicts_before = count_conflicts(before_sched)

            sched = baseline_random_schedule(n_adj)
            fitness = None
            history = None
            conflicts_after = count_conflicts(sched)
        elif choice == "Greedy (Heuristic)":
            naive = random_individual(n_adj)
            before_sched = pack_into_fixed_rounds(naive, n_adj)
            conflicts_before = count_conflicts(before_sched)

            sched = greedy_schedule(n_adj)
            fitness = None
            history = None
            conflicts_after = count_conflicts(sched)
        else:
            params = self._build_ga_params_from_ui()
            # show conflicts for a naive ordering before GA runs
            naive = random_individual(n_adj)
            before_sched = pack_into_fixed_rounds(naive, n_adj)
            conflicts_before = count_conflicts(before_sched)

            sched, fit, history = genetic_algorithm_schedule(n_adj, params)
            fitness = fit
            conflicts_after = count_conflicts(sched)

        elapsed = time.time() - start
        # if venues loaded, attach venues for display only
        try:
            sched_display = assign_venues(sched, self.venues) if getattr(self, 'venues', None) else sched
        except Exception:
            sched_display = sched

        out = schedule_to_string(sched_display, self.team_names)
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", out + "\n")
        if fitness is not None:
            self.result_text.insert("end", f"\nFitness: {fitness:.3f}\n")
        # show conflicts
        try:
            self.process_text.insert("end", f"Conflicts before: {conflicts_before}, after: {conflicts_after}\n")
        except Exception:
            pass
        # if GA produced a fitness history, plot it
        try:
            if 'history' in locals() and history:
                self._show_fitness_plot(history)
        except Exception:
            pass
        self.process_text.insert("end", f"Completed in {elapsed:.2f}s\n")
        self.status_var.set("Ready.")
        self.last_results = dict(algorithm=choice, num_teams=n_adj, schedule=sched, fitness=fitness, history=history if 'history' in locals() else None, time=elapsed)

    def run_both(self):
        """Run baseline + GA presets for comparison (3 trials minimum)."""
        try:
            n = int(self.num_teams_var.get())
        except Exception:
            messagebox.showerror("Input Error", "Please enter a valid number of teams.")
            return

        n_adj = add_bye_if_odd(n)
        self.process_text.insert("end", f"Running comparison on {n_adj} teams...\n")
        # Run baseline (greedy) once, and run GA with 3 presets one trial each
        results = []
        t0 = time.time()

        # Baseline greedy
        naive = random_individual(n_adj)
        before_sched = pack_into_fixed_rounds(naive, n_adj)
        conflicts_before = count_conflicts(before_sched)

        gb = greedy_schedule(n_adj)
        conflicts_after = count_conflicts(gb)
        results.append(("Greedy", gb, None, conflicts_before, conflicts_after, None))

        # Three GA presets
        presets = ["GA Default", "GA Large Population", "GA High Mutation"]
        for p in presets:
            self.preset_var.set(p)
            params = self._build_ga_params_from_ui()
            naive = random_individual(n_adj)
            before_sched = pack_into_fixed_rounds(naive, n_adj)
            cb = count_conflicts(before_sched)

            sched, fit, history = genetic_algorithm_schedule(n_adj, params)
            ca = count_conflicts(sched)
            results.append((p, sched, fit, cb, ca, history))

        total_time = time.time() - t0
        # Display summary
        self.compare_text.delete("1.0", "end")
        for name, sched, fit, cb, ca, history in results:
            self.compare_text.insert("end", f"--- {name} ---\n")
            # attach venues for display if available
            try:
                sched_disp = assign_venues(sched, self.venues) if getattr(self, 'venues', None) else sched
            except Exception:
                sched_disp = sched
            self.compare_text.insert("end", schedule_to_string(sched_disp, self.team_names) + "\n")
            self.compare_text.insert("end", f"Conflicts before: {cb}, after: {ca}\n")
            if fit is not None:
                self.compare_text.insert("end", f"Fitness: {fit:.3f}\n")
            # attach a small link to view plot (we'll show a hint)
            if history:
                self.compare_text.insert("end", f"(fitness history available — run Selected on that preset to view)\n")
            self.compare_text.insert("end", "\n")

        self.process_text.insert("end", f"Comparison finished in {total_time:.2f}s\n")
        self.last_results = dict(comparison=results, time=total_time)

    def save_results(self):
        if not self.last_results:
            messagebox.showinfo("No Results", "No results to save. Run an experiment first.")
            return

        fpath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not fpath:
            return

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("Results Export\n")
                f.write(str(self.last_results))
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save results: {e}")

    # (Theme support removed)

    def _show_fitness_plot(self, history):
        """Show GA fitness history (best per generation) in a new window."""
        if not HAS_MPL:
            self.process_text.insert("end", "Matplotlib not available; cannot show plot.\n")
            return
        win = tk.Toplevel(self)
        win.title("GA Fitness Progress")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(range(1, len(history) + 1), history, marker='o')
        ax.set_xlabel('Generation')
        ax.set_ylabel('Best Fitness')
        ax.set_title('GA Best Fitness per Generation')
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_teams(self):
        """Load team names from a simple text or CSV file (one name per line)."""
        fpath = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt;*.csv"), ("All files", "*.*")])
        if not fpath:
            return
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            # map indices 0..n-1 to names
            self.team_names = {i: name for i, name in enumerate(lines)}
            self.num_teams_var.set(len(lines))
            self.process_text.insert("end", f"Loaded {len(lines)} teams from {fpath}\n")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load teams: {e}")

    def load_venues(self):
        """Load venue names from a simple text/CSV file (one venue per line)."""
        fpath = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt;*.csv"), ("All files", "*.*")])
        if not fpath:
            return
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            self.venues = lines
            self.process_text.insert("end", f"Loaded {len(lines)} venues from {fpath}\n")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load venues: {e}")

    def show_greedy_graph(self):
        """Run multiple randomized-greedy trials and show distribution of number of rounds.

        This helps compare the deterministic greedy ordering vs randomized starts.
        """
        if not HAS_MPL:
            self.process_text.insert("end", "Matplotlib not available; cannot show greedy graph.\n")
            return

        try:
            n = int(self.num_teams_var.get())
        except Exception:
            messagebox.showerror("Input Error", "Please enter a valid number of teams.")
            return

        n_adj = add_bye_if_odd(n)
        trials = 30
        rounds_counts = []
        for _ in range(trials):
            indiv = random_individual(n_adj)
            sched = schedule_rounds_from_order(n_adj, indiv)
            rounds_counts.append(len(sched))

        # deterministic greedy
        try:
            greedy_sched = greedy_schedule(n_adj)
            greedy_rounds = len(greedy_sched)
        except Exception:
            greedy_rounds = None

        # plot
        win = tk.Toplevel(self)
        win.title("Greedy Trials: Rounds Distribution")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.boxplot(rounds_counts, vert=False)
        ax.set_xlabel('Number of Rounds')
        ax.set_yticks([])
        ax.set_title(f'Greedy (randomized starts) — {trials} trials (n={n_adj})')
        if greedy_rounds is not None:
            ax.axvline(greedy_rounds, color='red', linestyle='--', label=f'Deterministic greedy: {greedy_rounds}')
            ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.process_text.insert("end", f"Plotted greedy distribution over {trials} randomized starts.\n")
        
    def show_algorithm_distribution(self):
        """Run multiple trials of the selected algorithm and show distribution of number of rounds.

        For Baseline (Random): runs `baseline_random_schedule` multiple times.
        For Greedy: runs randomized starts (random_individual -> greedy packing) multiple times.
        For Genetic: runs the GA multiple times and collects the number of rounds per run.
        """
        if not HAS_MPL:
            self.process_text.insert("end", "Matplotlib not available; cannot show distribution.\n")
            return

        choice = self.algo_var.get()
        try:
            n = int(self.num_teams_var.get())
        except Exception:
            messagebox.showerror("Input Error", "Please enter a valid number of teams.")
            return

        n_adj = add_bye_if_odd(n)
        trials = 30
        rounds_counts = []

        self.process_text.insert("end", f"Running {trials} trials for '{choice}' (n={n_adj})...\n")

        if choice == "Baseline (Random)":
            for _ in range(trials):
                sched = baseline_random_schedule(n_adj)
                rounds_counts.append(len(sched))
            deterministic = None
        elif choice == "Greedy (Heuristic)":
            for _ in range(trials):
                indiv = random_individual(n_adj)
                # pack the randomized ordering greedily into rounds
                sched = schedule_rounds_from_order(n_adj, indiv)
                rounds_counts.append(len(sched))
            # deterministic greedy (single run using the greedy heuristic)
            try:
                deterministic = len(greedy_schedule(n_adj))
            except Exception:
                deterministic = None
        else:
            # Genetic Algorithm: run GA multiple times and record rounds
            params = self._build_ga_params_from_ui()
            for _ in range(trials):
                sched, fit, history = genetic_algorithm_schedule(n_adj, params)
                rounds_counts.append(len(sched))
            deterministic = None

        # plotting
        win = tk.Toplevel(self)
        win.title(f"Distribution - {choice}")
        fig, ax = plt.subplots(figsize=(6, 3))
        # show boxplot and histogram combined
        ax.boxplot(rounds_counts, vert=False)
        ax.set_xlabel('Number of Rounds')
        ax.set_yticks([])
        ax.set_title(f"{choice} — {trials} trials (n={n_adj})")
        if deterministic is not None:
            ax.axvline(deterministic, color='red', linestyle='--', label=f'Deterministic: {deterministic}')
            ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.process_text.insert("end", "Distribution plot ready.\n")

    def open_graph(self):
        """Open an appropriate graph for the last results or let user pick comparison entry.

        - If last_results contains GA `history`, plot fitness per generation.
        - If last_results contains a `comparison` list, prompt for an entry and plot its history or rounds.
        - Otherwise run a small set of trials for the selected algorithm and show distribution.
        """
        if not HAS_MPL:
            self.process_text.insert("end", "Matplotlib not available; cannot open graph.\n")
            return

        if not self.last_results:
            self.process_text.insert("end", "No previous results; running quick trials for selected algorithm...\n")
            self.show_algorithm_distribution()
            return

        # if comparison results exist, allow selecting one
        if 'comparison' in self.last_results:
            comp = self.last_results['comparison']
            try:
                import tkinter.simpledialog as sd
                sel_idx = sd.askinteger("Select entry", "Enter entry number to plot (1..%d):" % len(comp), minvalue=1, maxvalue=len(comp))
                if sel_idx is None:
                    return
                sel = comp[sel_idx - 1]
            except Exception:
                sel = comp[0]

            # sel: (name, sched, fit, cb, ca, history)
            history = None
            try:
                history = sel[5]
            except Exception:
                history = None

            if history:
                self._plot_fitness_history(history, title=f"{sel[0]} fitness history")
            else:
                rounds = [len(sel[1])]
                self._plot_rounds_distribution(rounds, title=f"{sel[0]} rounds (single)")
            return

        # single-run last_results
        if 'history' in self.last_results and self.last_results['history']:
            self._plot_fitness_history(self.last_results['history'], title=f"{self.last_results.get('algorithm')} fitness history")
            return

        # fallback: run quick trials for selected algorithm
        self.process_text.insert("end", "No history available; running quick trials for selected algorithm...\n")
        self.show_algorithm_distribution()

    def _plot_fitness_history(self, history, title="Fitness History"):
        win = tk.Toplevel(self)
        win.title(title)
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(range(1, len(history) + 1), history, marker='o')
        ax.set_xlabel('Generation')
        ax.set_ylabel('Best Fitness')
        ax.set_title(title)
        ax.grid(True)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _plot_rounds_distribution(self, rounds_list, title="Rounds Distribution"):
        win = tk.Toplevel(self)
        win.title(title)
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.boxplot(rounds_list, vert=False)
        ax.set_xlabel('Number of Rounds')
        ax.set_yticks([])
        ax.set_title(title)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        