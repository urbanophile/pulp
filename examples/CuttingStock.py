from pulp import *

# Problem data
BAR_LENGTH = 33.0  # meters

ITEMS = {
    1: {"length": 6.0, "demand": 144},
    2: {"length": 13.5, "demand": 105},
    3: {"length": 15.0, "demand": 72},
    4: {"length": 16.5, "demand": 30},
    5: {"length": 22.5, "demand": 24},
}


def generate_initial_patterns():
    """
    Generate initial single-item patterns.

    For each item type, create a pattern that cuts as many pieces of
    that type as possible from one bar.

    Returns:
        List of patterns, where each pattern is {item: count}
    """
    patterns = []
    for item_id, item_data in ITEMS.items():
        max_pieces = int(BAR_LENGTH // item_data["length"])
        pattern = {item_id: max_pieces}
        patterns.append(pattern)
    return patterns


def solve_master_problem(patterns, integer=False):
    """
    Solve the restricted master problem with current patterns.

    Args:
        patterns: List of cutting patterns
        integer: If True, solve as integer program; else LP relaxation

    Returns:
        (prob, pattern_vars, dual_prices)
    """
    prob = LpProblem("Master_Problem", LpMinimize)

    # Decision variables: how many bars to cut using each pattern
    cat = LpInteger if integer else LpContinuous
    pattern_vars = [
        LpVariable(f"Pattern_{i}", lowBound=0, cat=cat) for i in range(len(patterns))
    ]

    # Objective: minimize total number of bars used
    prob += lpSum(pattern_vars)

    # Constraints: meet demand for each item type
    for item_id in ITEMS.keys():
        demand = ITEMS[item_id]["demand"]
        prob += (
            lpSum(
                pattern_vars[i] * patterns[i].get(item_id, 0)
                for i in range(len(patterns))
            )
            >= demand,
            f"Demand_Item_{item_id}",
        )

    # Solve
    prob.solve(PULP_CBC_CMD(msg=0))

    # Extract dual prices (shadow prices) for LP relaxation
    dual_prices = {}
    if not integer and prob.status == LpStatusOptimal:
        for item_id in ITEMS.keys():
            constraint_name = f"Demand_Item_{item_id}"
            if constraint_name in prob.constraints:
                # Dual price (pi) is the shadow price of the constraint
                dual_prices[item_id] = prob.constraints[constraint_name].pi or 0.0

    return prob, pattern_vars, dual_prices


def solve_pricing_problem(dual_prices):
    """
    Solve the pricing subproblem to find an improving pattern.

    This is a knapsack problem: maximize the value of a pattern
    (based on dual prices) subject to bar length constraint.

    Args:
        dual_prices: Dict of {item_id: dual_price}

    Returns:
        (reduced_cost, pattern) or (None, None) if no improving pattern
    """
    prob = LpProblem("Pricing_Problem", LpMaximize)

    # Variables: how many pieces of each item to include in the pattern
    piece_vars = {}
    for item_id, item_data in ITEMS.items():
        max_pieces = int(BAR_LENGTH // item_data["length"])
        piece_vars[item_id] = LpVariable(
            f"Pieces_Item_{item_id}", lowBound=0, upBound=max_pieces, cat=LpInteger
        )

    # Objective: maximize dual value of the pattern
    prob += lpSum(
        dual_prices[item_id] * piece_vars[item_id] for item_id in ITEMS.keys()
    )

    # Constraint: total length must not exceed bar length
    prob += (
        lpSum(
            ITEMS[item_id]["length"] * piece_vars[item_id] for item_id in ITEMS.keys()
        )
        <= BAR_LENGTH
    )

    # Solve
    prob.solve(PULP_CBC_CMD(msg=0))

    if prob.status != LpStatusOptimal:
        return None, None

    # Calculate reduced cost = 1 - dual_value
    # (1 is the coefficient in the master problem objective)
    dual_value = value(prob.objective)
    reduced_cost = 1.0 - dual_value

    # If reduced cost < 0, we found an improving pattern
    if reduced_cost < -1e-6:  # small tolerance for numerical errors
        pattern = {}
        for item_id in ITEMS.keys():
            count = int(value(piece_vars[item_id]) + 0.5)  # round to nearest int
            if count > 0:
                pattern[item_id] = count
        return reduced_cost, pattern
    else:
        return None, None


def pattern_to_string(pattern):
    """Convert a pattern to a readable string."""
    parts = []
    for item_id in sorted(pattern.keys()):
        count = pattern[item_id]
        length = ITEMS[item_id]["length"]
        parts.append(f"{count}×{length}m")
    return " + ".join(parts)


def calculate_waste(pattern):
    """Calculate waste for a pattern."""
    used = sum(
        pattern.get(item_id, 0) * ITEMS[item_id]["length"] for item_id in ITEMS.keys()
    )
    return BAR_LENGTH - used


def print_patterns(patterns):
    """Print all patterns."""
    for i, pattern in enumerate(patterns):
        pattern_str = pattern_to_string(pattern)
        waste = calculate_waste(pattern)
        print(f"  Pattern {i+1}: {pattern_str:30s} (waste: {waste:.1f}m)")


def column_generation_solve():
    """
    Main column generation algorithm.

    Returns:
        (optimal_value, patterns, pattern_usage)
    """
    print("\n" + "=" * 70)
    print("COLUMN GENERATION ALGORITHM")
    print("=" * 70)

    # Step 1: Generate initial patterns (single-item patterns)
    patterns = generate_initial_patterns()
    print(f"\nInitial patterns (single-item):")
    print_patterns(patterns)

    iteration = 0

    # Step 2: Iterative improvement
    while True:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        # Solve master problem (LP relaxation)
        prob, pattern_vars, dual_prices = solve_master_problem(patterns, integer=False)

        if prob.status != LpStatusOptimal:
            print("Master problem not optimal!")
            break

        lp_value = value(prob.objective)
        print(f"LP value: {lp_value:.4f} bars")
        print(f"Dual prices: {dual_prices}")

        # Solve pricing problem to find improving pattern
        reduced_cost, new_pattern = solve_pricing_problem(dual_prices)

        if new_pattern is None:
            print("No improving pattern found - LP optimality reached!")
            print(f"\nFinal LP bound: {lp_value:.4f} bars")
            break

        # Add new pattern
        patterns.append(new_pattern)
        pattern_str = pattern_to_string(new_pattern)
        print(f"Adding pattern {len(patterns)}: {pattern_str}")
        print(f"Reduced cost: {reduced_cost:.6f}")

    # Step 3: Solve final integer program
    print(f"\n--- Solving Final Integer Program ---")
    print(f"Total patterns: {len(patterns)}")

    prob, pattern_vars, _ = solve_master_problem(patterns, integer=True)

    if prob.status != LpStatusOptimal:
        print("Integer program not optimal!")
        return None, patterns, {}

    optimal_value = int(value(prob.objective))
    print(f"Optimal integer solution: {optimal_value} bars")

    # Extract solution
    pattern_usage = {}
    for i, var in enumerate(pattern_vars):
        usage = value(var)
        if usage and usage > 0.001:  # numerical tolerance
            pattern_usage[i] = usage

    return optimal_value, patterns, pattern_usage


def print_solution(optimal_value, patterns, pattern_usage):
    """Print the final solution."""
    print("\n" + "=" * 70)
    print("OPTIMAL SOLUTION")
    print("=" * 70)
    print(f"\nTotal bars needed: {optimal_value}")
    print(f"\nCutting plan:")
    print("-" * 70)

    items_produced = {item_id: 0 for item_id in ITEMS.keys()}
    total_waste = 0

    for pattern_idx in sorted(pattern_usage.keys()):
        pattern = patterns[pattern_idx]
        times = pattern_usage[pattern_idx]

        pattern_str = pattern_to_string(pattern)
        waste = calculate_waste(pattern)

        # For LP solution, show fractional values
        if isinstance(times, float) and times != int(times):
            print(
                f"Pattern {pattern_idx+1:2d}: {pattern_str:30s} × {times:6.2f} bars  (waste: {waste:4.1f}m)"
            )
        else:
            times_int = int(times + 0.5)
            print(
                f"Pattern {pattern_idx+1:2d}: {pattern_str:30s} × {times_int:6d} bars  (waste: {waste:4.1f}m)"
            )
            times = times_int

        # Track production
        for item_id, count in pattern.items():
            items_produced[item_id] += count * times
        total_waste += waste * times

    print("-" * 70)
    print(f"\nTotal waste: {total_waste:.1f} meters")

    print("\nDemand satisfaction:")
    for item_id in sorted(ITEMS.keys()):
        produced = items_produced[item_id]
        demanded = ITEMS[item_id]["demand"]
        length = ITEMS[item_id]["length"]
        status = "✓" if produced >= demanded else "✗"
        print(
            f"  Item {item_id} ({length:4.1f}m): {produced:6.1f} produced (demand: {demanded:3d}) {status}"
        )


def main():
    """Run the column generation example."""
    print("=" * 70)
    print("ONE-DIMENSIONAL CUTTING STOCK PROBLEM")
    print("Column Generation Example (Gilmore & Gomory)")
    print("=" * 70)

    print(f"\nBar length: {BAR_LENGTH} meters")
    print("\nCustomer requirements:")
    print("  Item    Length(m)    Demand")
    print("  " + "-" * 32)
    for item_id in sorted(ITEMS.keys()):
        length = ITEMS[item_id]["length"]
        demand = ITEMS[item_id]["demand"]
        print(f"   {item_id}       {length:5.1f}       {demand:5d}")

    # Solve using column generation
    optimal_value, patterns, pattern_usage = column_generation_solve()

    # Print solution
    if optimal_value is not None:
        print_solution(optimal_value, patterns, pattern_usage)

    print("\n" + "=" * 70)
    print("=" * 70)
    print("• Started with 5 simple single-item patterns")
    print(f"• Column generation found {len(patterns)} useful patterns total")
    print(f"• Only {len(pattern_usage)} patterns used in optimal solution")
    print("=" * 70)


if __name__ == "__main__":
    main()
