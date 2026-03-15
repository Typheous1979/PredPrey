"""
Simulation Run Analyzer.

Takes the raw tick-by-tick population series from the database and produces
a structured AnalysisResult with computed metrics and descriptive narratives
for: hunting strategies, evasion strategies, plant/environment dynamics,
and overall ecosystem outcome.

All inference is derived purely from the (tick, prey, predators, plants)
time-series — no per-agent genome data required.
"""
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    run_id:          int
    total_ticks:     int
    outcome:         str     # "Coexistence" | "Prey Dominance" | "Predator Dominance" | "Ecosystem Collapse"

    # Stats
    peak_prey:         int
    peak_predators:    int
    mean_prey:         float
    mean_predators:    float
    mean_plants:       float
    prey_stability:    str   # "Stable" | "Moderately Volatile" | "Highly Volatile"
    oscillation:       Optional[str]   # None or "~N-tick cycles"
    prey_extinctions:  int
    pred_extinctions:  int

    # Late-run trends
    prey_late_trend:      str   # "Growing" | "Declining" | "Stable"
    predator_late_trend:  str
    plant_late_trend:     str

    # Narratives (HTML paragraphs)
    hunting_strategy:     str
    evasion_strategy:     str
    plant_environment:    str
    final_outcome:        str
    overall_assessment:   str


# ---------------------------------------------------------------------------
# Math helpers (no numpy required)
# ---------------------------------------------------------------------------

def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: list[float]) -> float:
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5 if xs else 0.0


def _cv(xs: list[float]) -> float:
    m = _mean(xs)
    return _std(xs) / m if m > 0 else 0.0


def _slope(xs: list[float]) -> float:
    """Linear regression slope (units per index step)."""
    n = len(xs)
    if n < 2:
        return 0.0
    indices = list(range(n))
    mx = _mean(indices)
    my = _mean(xs)
    num = sum((i - mx) * (y - my) for i, y in zip(indices, xs))
    den = sum((i - mx) ** 2 for i in indices)
    return num / den if den != 0 else 0.0


def _find_peaks(xs: list[float], window: int = 5, min_prom: float = 0.1) -> list[int]:
    """Return indices of local maxima with minimum prominence."""
    peaks = []
    max_val = max(xs) if xs else 1
    for i in range(window, len(xs) - window):
        if xs[i] == max(xs[i - window:i + window + 1]) and xs[i] > max_val * min_prom:
            peaks.append(i)
    return peaks


def _avg_period(peaks: list[int]) -> Optional[float]:
    if len(peaks) < 2:
        return None
    gaps = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    return round(_mean(gaps), 0)


def _late_trend(xs: list[float], threshold: float = 0.05) -> str:
    """Characterise the trend in the last 25% of a series."""
    n = len(xs)
    if n < 8:
        return "Stable"
    segment = xs[int(n * 0.75):]
    slope = _slope(segment)
    scale = _mean(xs) if _mean(xs) > 0 else 1
    rel = slope / scale
    if rel > threshold:
        return "Growing"
    if rel < -threshold:
        return "Declining"
    return "Stable"


def _count_recoveries(xs: list[float], low_frac: float = 0.2, min_gap: int = 5) -> int:
    """Count how many times the series recovered from a low (<low_frac of peak) to above 50% of peak."""
    if not xs:
        return 0
    peak = max(xs)
    low_thresh   = peak * low_frac
    high_thresh  = peak * 0.5
    recoveries, in_low, last_low = 0, False, -999
    for i, v in enumerate(xs):
        if v <= low_thresh:
            in_low = True
            last_low = i
        elif in_low and v >= high_thresh and i - last_low >= min_gap:
            recoveries += 1
            in_low = False
    return recoveries


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyse_run(
    run_id: int,
    rows: list[tuple[int, int, int, int]],   # (tick, prey, pred, plants)
) -> AnalysisResult:
    if not rows:
        raise ValueError("No data to analyse.")

    ticks  = [r[0] for r in rows]
    prey   = [float(r[1]) for r in rows]
    preds  = [float(r[2]) for r in rows]
    plants = [float(r[3]) for r in rows]
    n      = len(rows)

    # ── Outcome ────────────────────────────────────────────────────────
    final_prey = prey[-1]
    final_pred = preds[-1]
    if final_prey > 0 and final_pred > 0:
        outcome = "Coexistence"
    elif final_prey > 0 and final_pred == 0:
        outcome = "Prey Dominance"
    elif final_prey == 0 and final_pred > 0:
        outcome = "Predator Dominance"
    else:
        outcome = "Ecosystem Collapse"

    # ── Basic stats ────────────────────────────────────────────────────
    mean_prey  = _mean(prey)
    mean_preds = _mean(preds)
    mean_plants = _mean(plants)
    peak_prey  = int(max(prey))
    peak_preds = int(max(preds))

    # ── Stability ──────────────────────────────────────────────────────
    cv = _cv(prey)
    if cv < 0.25:
        prey_stability = "Stable"
    elif cv < 0.6:
        prey_stability = "Moderately Volatile"
    else:
        prey_stability = "Highly Volatile"

    # ── Oscillation ────────────────────────────────────────────────────
    peaks = _find_peaks(prey, window=max(3, n // 40), min_prom=0.15)
    period = _avg_period(peaks)
    oscillation = f"~{int(period)}-tick cycles" if period else None

    # ── Extinction events ──────────────────────────────────────────────
    prey_ext = sum(1 for i in range(1, n) if prey[i] == 0 and prey[i - 1] > 0)
    pred_ext = sum(1 for i in range(1, n) if preds[i] == 0 and preds[i - 1] > 0)
    recoveries = _count_recoveries(prey)

    # ── Late-run trends ────────────────────────────────────────────────
    prey_late   = _late_trend(prey)
    pred_late   = _late_trend(preds)
    plant_late  = _late_trend(plants)

    # ── Predator/prey ratio ────────────────────────────────────────────
    ratios = [p / (q + 1) for p, q in zip(preds, prey)]
    mean_ratio = _mean(ratios)
    peak_ratio = max(ratios)

    # ── Phase lag (predator peaks lag behind prey peaks) ───────────────
    pred_peaks = _find_peaks(preds, window=max(3, n // 40), min_prom=0.15)
    lag_ticks: Optional[float] = None
    if len(peaks) >= 2 and len(pred_peaks) >= 2:
        lags = []
        for pp in pred_peaks:
            nearest = min(peaks, key=lambda pk: abs(pk - pp))
            if pp > nearest:
                lags.append(pp - nearest)
        if lags:
            lag_ticks = round(_mean(lags), 0)

    # ── Plant pressure ─────────────────────────────────────────────────
    if mean_plants > 0:
        plant_cv = _cv(plants)
        plant_peak_frac = max(plants) / (mean_plants + 1)
    else:
        plant_cv = 0.0
        plant_peak_frac = 1.0

    # ── Generate narratives ────────────────────────────────────────────
    hunting   = _hunting_narrative(
        outcome, mean_ratio, peak_ratio, mean_preds, peak_preds,
        mean_prey, pred_late, lag_ticks, pred_ext, n
    )
    evasion   = _evasion_narrative(
        outcome, prey_stability, cv, recoveries, prey_ext, prey_late,
        mean_ratio, oscillation, peaks, n
    )
    plant_env = _plant_narrative(
        mean_plants, plant_late, plant_cv, mean_prey, plant_peak_frac, n
    )
    final_out = _outcome_narrative(
        outcome, final_prey, final_pred, plants[-1],
        prey_late, pred_late, ticks[-1]
    )
    overall   = _overall_narrative(
        outcome, prey_stability, oscillation, mean_ratio,
        recoveries, prey_ext, pred_ext, plant_late
    )

    return AnalysisResult(
        run_id=run_id,
        total_ticks=ticks[-1],
        outcome=outcome,
        peak_prey=peak_prey,
        peak_predators=peak_preds,
        mean_prey=round(mean_prey, 1),
        mean_predators=round(mean_preds, 1),
        mean_plants=round(mean_plants, 1),
        prey_stability=prey_stability,
        oscillation=oscillation,
        prey_extinctions=prey_ext,
        pred_extinctions=pred_ext,
        prey_late_trend=prey_late,
        predator_late_trend=pred_late,
        plant_late_trend=plant_late,
        hunting_strategy=hunting,
        evasion_strategy=evasion,
        plant_environment=plant_env,
        final_outcome=final_out,
        overall_assessment=overall,
    )


# ---------------------------------------------------------------------------
# Narrative generators
# ---------------------------------------------------------------------------

def _hunting_narrative(
    outcome, mean_ratio, peak_ratio, mean_preds, peak_preds,
    mean_prey, pred_late, lag_ticks, pred_ext, n
) -> str:
    parts = []

    if pred_ext > 0:
        parts.append(
            f"Predators suffered {pred_ext} extinction event(s) during this run, "
            "indicating that their hunting strategies were repeatedly overwhelmed by prey "
            "defenses or insufficient food supply. Each extinction wiped out accumulated "
            "genetic adaptations, forcing the population to re-evolve from reintroduced stock."
        )

    if mean_ratio < 0.05:
        parts.append(
            "Predators were significantly outnumbered throughout the run "
            f"(average predator-to-prey ratio: {mean_ratio:.3f}). This sparse predator density "
            "suggests an ambush or stealth-based hunting strategy — individual predators "
            "operating independently rather than coordinating, relying on patience and "
            "positioning over overwhelming numbers."
        )
    elif mean_ratio < 0.15:
        parts.append(
            f"With a moderate predator-to-prey ratio of {mean_ratio:.3f}, predators maintained "
            "enough numbers to apply consistent pressure without depleting their food supply. "
            "This balance is characteristic of pursuit hunters: predators that actively chase "
            "prey across the grid and rely on stamina and speed rather than ambush."
        )
    elif mean_ratio < 0.4:
        parts.append(
            f"A high predator-to-prey ratio ({mean_ratio:.3f} on average, peaking at {peak_ratio:.2f}) "
            "indicates aggressive pack-style pressure. Predators maintained population densities "
            "that saturated hunting territory, leaving prey with few safe zones. "
            "This strategy succeeds when prey are slow to reproduce but risks ecosystem collapse "
            "if prey numbers crash."
        )
    else:
        parts.append(
            f"The predator-to-prey ratio was extremely high ({mean_ratio:.3f}), suggesting "
            "a boom-and-bust hunting pattern where predators overcrowded the environment "
            "during prey abundance. This overhunting strategy produces rapid prey depletion "
            "followed by predator starvation — a classic sign of unconstrained aggression "
            "without adaptive resource management."
        )

    if lag_ticks is not None:
        parts.append(
            f"Predator population peaks lagged behind prey peaks by approximately {int(lag_ticks)} ticks, "
            "a hallmark of reactive hunting — predators respond to prey abundance rather than "
            "anticipating it. Shorter lags indicate faster-reproducing or more opportunistic hunters; "
            f"this {int(lag_ticks)}-tick lag suggests "
            + ("rapid adaptation." if lag_ticks < 20 else
               "moderate responsiveness." if lag_ticks < 50 else
               "slow generational turnover in predator strategy.")
        )

    if pred_late == "Growing":
        parts.append(
            "In the final phase of the run, predator numbers were still climbing — "
            "hunting strategies were actively succeeding and had not yet hit resource limits."
        )
    elif pred_late == "Declining":
        parts.append(
            "By the end of the run, predator numbers were declining despite continued prey "
            "presence, suggesting prey evasion adaptations were beginning to outpace predator "
            "hunting efficiency — an evolutionary arms race tilting in the prey's favor."
        )

    return " ".join(parts) if parts else "Insufficient data to characterise hunting strategy."


def _evasion_narrative(
    outcome, prey_stability, cv, recoveries, prey_ext, prey_late,
    mean_ratio, oscillation, peaks, n
) -> str:
    parts = []

    if prey_ext > 0:
        parts.append(
            f"Prey populations collapsed to extinction {prey_ext} time(s), indicating that "
            "evasion strategies repeatedly failed under predator pressure. Each collapse "
            "reset the prey genome, preventing the accumulation of effective survival traits "
            "across generations."
        )

    if prey_stability == "Stable":
        parts.append(
            f"Prey maintained a stable population (coefficient of variation: {cv:.2f}), "
            "suggesting that evasion adaptations — likely a combination of camouflage, "
            "speed, and spatial awareness — were sufficient to absorb predator pressure "
            "without dramatic crashes. Stable prey populations typically reflect a mature "
            "evasion strategy that has reached equilibrium with predator capabilities."
        )
    elif prey_stability == "Moderately Volatile":
        parts.append(
            f"Prey populations oscillated with moderate volatility (CV: {cv:.2f}), "
            "indicating a developing but not fully optimised evasion strategy. "
            "The population absorbed predator surges but required significant recovery periods, "
            "pointing toward a boom-bust survival approach: high reproduction rates compensating "
            "for individual vulnerability rather than preventing capture outright."
        )
    else:
        parts.append(
            f"Prey populations were highly volatile (CV: {cv:.2f}), swinging between booms "
            "and near-crashes. This pattern suggests evasion strategies were reactive rather "
            "than proactive — prey relied on sheer reproductive speed to survive rather than "
            "individual-level evasion traits. Populations would boom when predator pressure "
            "lifted, then crash as predators adapted to exploit the abundance."
        )

    if recoveries > 0:
        parts.append(
            f"Prey recovered from critically low populations {recoveries} time(s) during this run. "
            "Each recovery demonstrates reproductive resilience — a key evasion meta-strategy "
            "where species-level survival is prioritised over individual survival. "
            + ("Frequent recoveries indicate prey genetics were optimising for rapid reproduction "
               "under pressure." if recoveries > 2 else
               "This resilience prevented extinction despite significant predator pressure.")
        )

    if oscillation and len(peaks) >= 3:
        parts.append(
            f"The prey population cycled in {oscillation}, a pattern consistent with "
            "prey that have evolved threshold-based evasion: populations suppress their "
            "reproduction and increase evasion behaviour when predator density crosses "
            "a certain level, only resuming growth once the threat recedes."
        )

    if prey_late == "Growing" and outcome != "Prey Dominance":
        parts.append(
            "In the final stretch of the run, prey numbers were increasing — evasion "
            "adaptations were outpacing predator hunting efficiency, and the prey population "
            "was establishing a stronger long-term position."
        )
    elif prey_late == "Declining" and outcome != "Predator Dominance":
        parts.append(
            "Prey numbers trended downward in the final phase, suggesting predators were "
            "gaining an evolutionary edge and prey evasion strategies had not adapted "
            "quickly enough to counter improved hunting behaviours."
        )

    return " ".join(parts) if parts else "Insufficient data to characterise evasion strategy."


def _plant_narrative(
    mean_plants, plant_late, plant_cv, mean_prey, plant_peak_frac, n
) -> str:
    parts = []

    if mean_plants < 1:
        parts.append(
            "Plant levels were near zero for most of the run, indicating severe overgrazing. "
            "Prey consumed vegetation faster than it could regrow, creating a food-scarce "
            "environment that limited maximum prey population size independently of predation. "
            "This secondary pressure likely drove prey to evolve higher mobility or lower "
            "metabolic demands to survive on minimal food intake."
        )
    elif mean_plants < mean_prey * 0.5:
        parts.append(
            f"Plants were consistently scarce relative to prey numbers (average: {mean_plants:.0f} plants). "
            "Prey grazed heavily on available vegetation, suggesting foraging efficiency was "
            "a key survival trait. Competition for food among prey may have driven selection "
            "for faster movement, better plant detection range, or lower energy consumption."
        )
    elif mean_plants > mean_prey * 3:
        parts.append(
            f"Plant resources were abundant and underutilised (average: {mean_plants:.0f} plants). "
            "This suggests prey were spending more energy on evasion than foraging — either "
            "predator pressure was high enough to keep prey from safely grazing, or prey "
            "populations were too low to consume available food. Excess plant cover may have "
            "also provided natural concealment, indirectly aiding evasion."
        )
    else:
        parts.append(
            f"Plants maintained a moderate presence throughout the run (average: {mean_plants:.0f}), "
            "suggesting balanced consumption. Prey grazed efficiently without stripping "
            "the environment, and plant regrowth kept pace with consumption. This balance "
            "indicates the ecosystem had found a stable energy flow from plants to prey to predators."
        )

    if plant_cv > 0.4:
        parts.append(
            "Plant populations showed significant volatility, cycling in response to prey "
            "population booms and crashes. High prey numbers stripped vegetation, which then "
            "reduced prey carrying capacity — a delayed feedback loop that amplified "
            "population oscillations throughout the ecosystem."
        )
    elif plant_cv < 0.15:
        parts.append(
            "Plant levels were remarkably stable across the entire run, suggesting that "
            "prey consumption and plant regrowth reached a steady equilibrium early on. "
            "A stable plant base provides a consistent energy foundation that supports "
            "more predictable prey and predator population dynamics."
        )

    if plant_late == "Declining":
        parts.append(
            "By the end of the run, plant coverage was declining — likely driven by growing "
            "prey populations outpacing regrowth rates. Without intervention (higher regrowth "
            "ticks or lower plant energy per cell), continued overgrazing would eventually "
            "collapse the food supply and trigger a prey population crash."
        )
    elif plant_late == "Growing":
        parts.append(
            "Plant coverage was recovering at the end of the run, indicating that prey "
            "pressure on vegetation had eased — either due to declining prey numbers or "
            "prey shifting their foraging patterns."
        )

    return " ".join(parts) if parts else "Insufficient plant data to characterise environment."


def _outcome_narrative(
    outcome, final_prey, final_pred, final_plants, prey_late, pred_late, total_ticks
) -> str:
    if outcome == "Coexistence":
        return (
            f"After {total_ticks} ticks, both populations remained active: "
            f"{int(final_prey)} prey and {int(final_pred)} predators, with "
            f"{int(final_plants)} plant cells alive. The ecosystem achieved coexistence — "
            "neither species drove the other to extinction. "
            + ("Both populations were still shifting at the end of the run, suggesting "
               "the ecosystem had not yet fully stabilised." if prey_late != "Stable" or pred_late != "Stable" else
               "Population levels had stabilised, indicating a mature and self-sustaining ecosystem.")
        )
    elif outcome == "Prey Dominance":
        return (
            f"Predators went extinct before the run ended, leaving {int(final_prey)} prey "
            f"and {int(final_plants)} plant cells at tick {total_ticks}. Without predation "
            "pressure, prey population growth is now limited only by food availability and "
            "the carrying capacity of the environment. This outcome typically follows a period "
            "where prey evasion evolved faster than predator hunting — predators could no longer "
            "catch enough food to sustain reproduction."
        )
    elif outcome == "Predator Dominance":
        return (
            f"Prey were driven to extinction, leaving {int(final_pred)} predators at tick "
            f"{total_ticks} with {int(final_plants)} plant cells remaining. Without prey, "
            "predators will inevitably starve. This overhunting outcome is typical when "
            "predators evolve high hunting efficiency before prey can develop effective evasion, "
            "or when the predator population grew too rapidly relative to prey reproduction rates."
        )
    else:
        return (
            f"Both prey and predators reached extinction by tick {total_ticks}. "
            "Ecosystem collapse typically follows a cascade: predators overhunt prey to extinction, "
            "then starve without a food source. The absence of plant activity at the end "
            f"({int(final_plants)} plants) suggests vegetation may have also been depleted, "
            "accelerating the collapse."
        )


def _overall_narrative(
    outcome, prey_stability, oscillation, mean_ratio,
    recoveries, prey_ext, pred_ext, plant_late
) -> str:
    stability_adj = {
        "Stable": "stable and well-balanced",
        "Moderately Volatile": "dynamic with periodic instability",
        "Highly Volatile": "turbulent and evolutionarily volatile",
    }.get(prey_stability, "active")

    osc_str = (
        f"Classic Lotka-Volterra oscillations emerged ({oscillation}), "
        "reflecting a healthy predator-prey feedback loop. "
    ) if oscillation else (
        "Population dynamics did not settle into regular oscillatory cycles, "
        "suggesting the ecosystem was still evolving toward equilibrium or "
        "that one species held a consistent upper hand. "
    )

    event_str = ""
    if prey_ext > 0 or pred_ext > 0:
        event_str = (
            f"The run included {prey_ext} prey extinction(s) and {pred_ext} predator "
            f"extinction(s), indicating a volatile evolutionary environment where neither "
            f"species fully stabilised its strategies. "
        )

    recovery_str = (
        f"Prey demonstrated strong resilience, recovering {recoveries} time(s) from "
        "near-extinction, which points to robust reproductive genetics. "
    ) if recoveries > 1 else ""

    plant_str = (
        "Plant resources were under pressure at run end, which may limit long-term sustainability. "
    ) if plant_late == "Declining" else ""

    conclusion = {
        "Coexistence": (
            "Overall this run produced a functioning predator-prey ecosystem. Both species "
            "coexisted across the full run, with evolutionary pressures shaping both hunting "
            "and evasion strategies in tandem. This is the most ecologically rich outcome "
            "and the ideal starting point for parameter tuning and strategy comparison."
        ),
        "Prey Dominance": (
            "Overall this run ended in prey dominance — a clear win for evasion over hunting. "
            "To restore balance in future runs, consider increasing predator reproduction "
            "energy efficiency, lowering the predator reproduction threshold, or reducing "
            "prey camouflage traits to give predators a better chance of catching up."
        ),
        "Predator Dominance": (
            "Overall predators dominated this run, ultimately overhunting prey to extinction. "
            "To rebalance, consider increasing prey reproduction speed (lower reproduction "
            "energy threshold), increasing prey vision range, or reducing predator strength "
            "and metabolism efficiency to slow hunting pressure."
        ),
        "Ecosystem Collapse": (
            "Overall the ecosystem collapsed entirely. To prevent this in future runs, "
            "consider reducing predator-to-prey initial ratios, lowering predator "
            "reproduction rates, increasing plant density and regrowth speed, or "
            "raising the predator reproduction energy threshold to slow their growth."
        ),
    }.get(outcome, "")

    return f"This run was {stability_adj}. {osc_str}{event_str}{recovery_str}{plant_str}{conclusion}"
