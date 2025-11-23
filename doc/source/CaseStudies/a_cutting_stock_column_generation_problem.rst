A Cutting Stock Column Generation Problem
=================================================================

The Sponge Roll Problem
------------------------

This example demonstrates column generation using the Sponge Roll Problem,
a simplified one-dimensional cutting stock problem.

Problem Description
-------------------
A manufacturer produces rolls of sponge material (foam) in a standard length of 20 cm.
Customers order smaller pieces of various lengths, so the manufacturer must cut the
standard 20cm rolls into the required sizes while minimizing waste.

**Standard roll:** 20 cm (the "stock" being cut)

**Customer requirements:**

=====  ==========  ============
Size   Length(cm)  Pieces Needed
=====  ==========  ============
Small      5           150
Medium     7           200
Large      9           300
=====  ==========  ============

**Objective:** Minimize the number of 20cm rolls needed to satisfy all demand.

Why This Problem is Hard
^^^^^^^^^^^^^^^^^^^^^^^^^
The challenge is that there are many ways to cut a 20cm roll. For example:

- Pattern A: 4 small = 4*5 = 20cm (no waste)
- Pattern B: 2 medium + 1 small = 14 + 5 = 19cm (1cm waste)
- Pattern C: 2 large = 2*9 = 18cm (2cm waste)


Even for this simple problem with 3 sizes, there are dozens of valid cutting patterns.
For larger problems with more sizes and longer rolls, enumerating all patterns
becomes computationally infeasible—the number grows exponentially.

Solution Approach: Column Generation
-------------------------------------
Rather than enumerating all possible cutting patterns upfront, we use column
generation to generate patterns as needed:

1. **Start simple:** Begin with basic single-item patterns (e.g., a pattern with only 5cm pieces)
2. **Solve restricted problem:** Solve the master problem using only current patterns (LP relaxation)
3. **Check for improvements:** Use dual prices from the master problem to solve a "pricing subproblem" (knapsack)
4. **Add improving pattern:** If the subproblem finds a pattern with negative reduced cost, add it
5. **Repeat:** Continue until no improving patterns exist
6. **Final solve:** Solve the integer program with all generated patterns

This approach generates only the patterns actually needed for an optimal solution,
rather than all possible patterns.

Key Concepts
^^^^^^^^^^^^

**Master Problem:**
  Decides how many times to use each known pattern to minimize rolls used while meeting demand

**Pricing Subproblem:**
  A knapsack problem that finds the most "valuable" new pattern based on current dual prices

**Dual Prices (Shadow Prices):**
  Indicate how much the objective would improve if we could satisfy one more unit of demand for each size

**Reduced Cost:**
  The change in objective value from using a new pattern. Negative reduced cost means improvement.

