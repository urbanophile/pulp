# CLAUDE.md - PuLP Developer Guide for AI Assistants

> **Last Updated**: 2025-12-26
> **PuLP Version**: 3.3.0
> **Purpose**: Comprehensive guide for AI assistants working with the PuLP codebase

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Core Architecture](#core-architecture)
4. [Key Classes and Relationships](#key-classes-and-relationships)
5. [Solver API Architecture](#solver-api-architecture)
6. [Development Workflows](#development-workflows)
7. [Testing](#testing)
8. [Code Conventions](#code-conventions)
9. [Common Tasks](#common-tasks)
10. [Important Gotchas](#important-gotchas)

---

## Project Overview

**PuLP** is a linear and mixed-integer programming (MILP) modeler written in Python. It provides a high-level interface for creating optimization problems and solving them with various open-source and commercial solvers.

### Key Facts

- **Language**: Python 3.9+
- **License**: MIT
- **Project**: Part of COIN-OR (Computational Infrastructure for Operations Research)
- **Main Use Case**: Creating and solving LP/MILP optimization problems
- **Architecture**: Modeler + Solver API abstraction layer

### Core Capabilities

- Define optimization problems using Python objects (variables, constraints, objectives)
- Support for 25+ solvers (CBC, GLPK, CPLEX, Gurobi, HiGHS, SCIP, etc.)
- Generate MPS/LP format files
- Serialize/deserialize problems to JSON
- Bundled CBC solver for out-of-the-box functionality

---

## Repository Structure

```
pulp/
├── .github/
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── workflows/               # CI/CD pipelines
│   │   ├── pythonpackage.yml   # Main test workflow
│   │   ├── build_docs.yml      # Documentation builds
│   │   └── publish-to-test-pypi.yml
│   └── ISSUE_TEMPLATE/         # GitHub issue templates
├── doc/
│   └── source/                 # Sphinx documentation (RST)
│       ├── index.rst
│       ├── main/               # User guides
│       ├── technical/          # API reference
│       ├── develop/            # Developer docs
│       ├── CaseStudies/        # Tutorial examples
│       └── plugins/            # Third-party integrations
├── examples/                   # 17+ example scripts
├── pulp/                       # Main package
│   ├── __init__.py            # Package entry point
│   ├── pulp.py                # Core modeling classes (2,500+ lines)
│   ├── constants.py           # Global constants and enums
│   ├── utilities.py           # Helper functions (value, lpSum, lpDot)
│   ├── sparse.py              # Sparse matrix implementation
│   ├── mps_lp.py             # MPS/LP format handling
│   ├── apis/                  # Solver integration layer
│   │   ├── core.py           # Base LpSolver classes
│   │   ├── coin_api.py       # CBC solver
│   │   ├── gurobi_api.py     # Gurobi
│   │   ├── cplex_api.py      # CPLEX
│   │   ├── highs_api.py      # HiGHS
│   │   └── ...               # 12+ other solvers
│   ├── solverdir/            # Bundled CBC binaries
│   │   └── cbc/
│   │       ├── linux/        # i32, i64, arm64
│   │       ├── win/          # i32, i64
│   │       └── osx/          # i64
│   └── tests/
│       ├── test_pulp.py      # Main test suite (93KB)
│       ├── test_examples.py  # Example validation
│       ├── test_sparse.py    # Sparse matrix tests
│       ├── test_lpdot.py     # lpDot tests
│       └── run_tests.py      # Test runner
├── pyproject.toml             # Modern Python packaging config
├── README.rst                 # Project README
├── .pre-commit-config.yaml   # Code quality hooks
└── LICENSE                    # MIT license

```

---

## Core Architecture

PuLP uses a **layered architecture** separating problem modeling from solver execution:

```
┌─────────────────────────────────────────────────────────┐
│  User Code: Define Variables, Constraints, Objective    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Modeling Layer (pulp.py)                               │
│  - LpVariable, LpAffineExpression, LpConstraint         │
│  - LpProblem (problem container & solve orchestration)  │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Format Layer (mps_lp.py)                               │
│  - Convert to MPS/LP file formats                       │
│  - Serialize to/from JSON/Dict                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  Solver API Layer (apis/*.py)                           │
│  - Abstract LpSolver interface                          │
│  - Concrete implementations for each solver             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  External Solvers (CBC, Gurobi, CPLEX, HiGHS, etc.)    │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Used

1. **Template Method**: `LpSolver` defines solve workflow, subclasses implement `actualSolve()`
2. **Strategy Pattern**: Different solver implementations are interchangeable
3. **Fluent API**: Problem building using `+=` operators
4. **Operator Overloading**: Natural expression syntax (`x + y <= 5`)
5. **Sparse Representation**: Dict-based for memory efficiency

---

## Key Classes and Relationships

### Class Hierarchy

```python
# Core Modeling Classes (pulp.py)
LpElement                           # Base class for variables/constraints
├── LpVariable                      # Decision variable (x, y, z, ...)
└── LpConstraintVar                 # Column-wise constraint (column generation)

LpAffineExpression                  # Linear expression: 3*x + 2*y + 5
    # Dict[LpVariable, coefficient]

LpConstraint                        # Constraint: 3*x + 2*y <= 10
├── LpFractionConstraint           # Fraction: (num_expr)/(den_expr) <= RHS

LpProblem                          # Optimization problem container
├── FixedElasticSubProblem        # Constraint relaxation with penalties
    └── FractionElasticSubProblem  # Elastic constraints for fractions

# Solver Classes (apis/core.py, apis/*.py)
LpSolver                           # Abstract solver base
├── LpSolver_CMD                   # Command-line solver base
│   ├── PULP_CBC_CMD              # Default bundled solver
│   ├── COIN_CMD                  # COIN-OR CBC
│   ├── GLPK_CMD                  # GLPK
│   ├── CPLEX_CMD                 # CPLEX via CLI
│   ├── GUROBI_CMD                # Gurobi via CLI
│   ├── XPRESS_CMD                # Xpress via CLI
│   ├── HiGHS_CMD                 # HiGHS via CLI
│   └── ...                        # 15+ more solvers
└── Direct Python API Solvers
    ├── GUROBI                     # Gurobi via gurobipy
    ├── CPLEX_PY                   # CPLEX via cplex module
    ├── XPRESS                     # Xpress via xpress module
    ├── HiGHS                      # HiGHS via highspy
    ├── SCIP_PY                    # SCIP via pyscipopt
    ├── MOSEK                      # MOSEK via mosek module
    └── ...                        # 10+ more solvers

# Format Classes (mps_lp.py)
@dataclass MPS                     # MPS format representation
@dataclass MPSVariable             # Variable in MPS
@dataclass MPSConstraint           # Constraint in MPS
```

### Key Relationships

```python
# Problem Structure
LpProblem
├── .objective: LpAffineExpression
├── .constraints: Dict[str, LpConstraint]
├── .variables(): List[LpVariable]
└── .solve(solver): calls solver.solve(self)

# Constraint Structure
LpConstraint
├── .sense: int (-1/0/1 for <=, =, >=)
├── .constant: float (RHS value)
└── coefficient dict: LpAffineExpression

# Expression Structure
LpAffineExpression (dict)
├── key: LpVariable
└── value: coefficient (float)

# Solver Workflow
prob.solve(solver)
    → solver.solve(prob)
        → solver.actualSolve(prob)
            → Generate MPS/LP file
            → Call external solver binary
            → Parse solution file
            → Update prob.status, var.varValue, var.dj
```

---

## Solver API Architecture

### Two Integration Patterns

#### Pattern 1: Command-Line Solvers (LpSolver_CMD)

**Use Case**: External solver binaries (cbc, glpsol, cplex CLI)

**Workflow**:
```python
class SOLVER_CMD(LpSolver_CMD):
    def available(self):
        # Check if solver binary exists
        return shutil.which(self.path) is not None

    def actualSolve(self, lp):
        # 1. Create temp files
        self.create_tmp_files(...)

        # 2. Write problem to LP/MPS format
        lp.writeLP(tmpLp)

        # 3. Build command line
        cmd = [self.path, options, tmpLp, tmpSol]

        # 4. Execute solver
        subprocess.run(cmd)

        # 5. Parse solution file
        self.parse_output()

        # 6. Update LpProblem with results
        lp.status = LpStatusOptimal
        for var in lp.variables():
            var.varValue = solution[var.name]

        # 7. Cleanup temp files
        self.delete_tmp_files()
```

#### Pattern 2: Direct Python API (LpSolver)

**Use Case**: Native Python bindings (gurobipy, cplex, xpress)

**Workflow**:
```python
class SOLVER(LpSolver):
    def actualSolve(self, lp):
        # 1. Create native solver model
        model = gurobi.Model()

        # 2. Create solver variables
        for var in lp.variables():
            var.solverVar = model.addVar(...)

        # 3. Add constraints
        for name, constraint in lp.constraints.items():
            constraint.solverConstraint = model.addConstr(...)

        # 4. Set objective
        model.setObjective(objective_expr)

        # 5. Solve
        model.optimize()

        # 6. Extract solution
        lp.status = convertStatus(model.status)
        for var in lp.variables():
            var.varValue = var.solverVar.X

        # 7. Store model for warm starts
        lp.solverModel = model
```

### Required Solver Methods

Every solver MUST implement:

```python
class NewSolver(LpSolver):
    name = "SOLVER_NAME"  # Unique identifier

    def available(self):
        """Check if solver is installed and accessible"""
        return True/False

    def actualSolve(self, lp):
        """Core solving logic"""
        # Implement solving workflow
        # Update lp.status and var.varValue
        return status

    def actualResolve(self, lp, **kwargs):
        """Warm-start solving (optional, defaults to actualSolve)"""
        return self.actualSolve(lp)
```

### Common Solver Options

All solvers support these standard options (passed to `__init__`):

```python
solver = SOLVER(
    mip=True,           # Enable MIP (vs LP only)
    msg=True,           # Display solver output
    timeLimit=300,      # Time limit in seconds
    gapRel=0.01,       # Relative MIP gap tolerance
    gapAbs=1e-6,       # Absolute MIP gap tolerance
    options=[],         # Solver-specific options list
    keepFiles=False,    # Keep temp files (debugging)
    warmStart=False,    # Use warm start if available
    logPath=None,       # Log file path
)
```

---

## Development Workflows

### Initial Setup

```bash
# Clone repository
git clone https://github.com/coin-or/pulp.git
cd pulp

# Install in development mode with dev dependencies
python -m pip install -e .
python -m pip install --group=dev .

# Setup pre-commit hooks
pre-commit install
```

### Code Quality Tools

#### Black (Code Formatting)

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .
```

**Configuration** (pyproject.toml):
- Line length: 88
- Target: Python 3.7+
- Excludes: build/, .venv/, .git/

#### MyPy (Type Checking)

```bash
# Type check the codebase
mypy pulp/

# Specific file
mypy pulp/pulp.py
```

**Configuration** (pyproject.toml):
- Excludes: `pulp/solverdir/`, `.venv/`, `build/`
- `warn_unused_ignores = true`
- Follows imports except pulp modules

#### Pre-commit Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run on staged files (automatic on git commit)
pre-commit run
```

**Hooks**:
1. **black**: Auto-format code
2. **pyupgrade**: Modernize syntax to Python 3.7+

### Building Documentation

```bash
# Install documentation dependencies
pip install --group=dev .

# Build HTML docs
cd doc
make html

# View documentation
# Open: doc/build/html/index.html in browser
```

**Documentation Framework**: Sphinx with Read-the-Docs theme

**Source Files**: `doc/source/*.rst` (reStructuredText)

**Key Documentation Sections**:
- `main/`: User installation and configuration guides
- `technical/`: API reference (auto-generated from docstrings)
- `develop/`: Contributing and development guides
- `CaseStudies/`: Tutorial examples with full code

---

## Testing

### Running Tests

```bash
# Run all tests (includes solver availability checks)
pulptest

# Or manually
python -m pulp.tests.run_tests

# Run specific test file
python -m pytest pulp/tests/test_pulp.py

# Run specific test class
python -m pytest pulp/tests/test_pulp.py::PULP_CBC_CMDTest

# Run specific test method
python -m pytest pulp/tests/test_pulp.py::PULP_CBC_CMDTest::test_continuous
```

### Test Organization

**Main Test File**: `pulp/tests/test_pulp.py` (93KB, 2,000+ lines)

**Structure**:
```python
class BaseSolverTest:
    class PuLPTest(unittest.TestCase):
        # Base test suite with 40+ test methods
        def test_continuous(self): ...
        def test_MIP(self): ...
        def test_export_dict(self): ...
        # etc.

# Solver-specific test classes (inherit PuLPTest)
class PULP_CBC_CMDTest(BaseSolverTest.PuLPTest):
    solverClass = PULP_CBC_CMD

class GUROBITest(BaseSolverTest.PuLPTest):
    solverClass = GUROBI

# ... one class per solver
```

### Writing Tests for New Features

**Location**: Add to `pulp/tests/test_pulp.py` in `BaseSolverTest.PuLPTest`

**Template**:
```python
def test_my_new_feature(self):
    """Test description"""
    if not self.solver.available():
        self.skipTest(f"{self.solver.name} not available")

    # Setup problem
    prob = LpProblem("test", LpMinimize)
    x = LpVariable("x", 0, 4)
    y = LpVariable("y", 0, 3)

    # Add constraints and objective
    prob += x + y <= 5
    prob += 2*x + y

    # Solve
    status = prob.solve(self.solver)

    # Assertions
    self.assertEqual(status, LpStatusOptimal)
    self.assertAlmostEqual(value(x), 2.0)
    self.assertAlmostEqual(value(y), 3.0)
```

### Test Files

| File | Purpose |
|------|---------|
| `test_pulp.py` | Main solver and modeling tests |
| `test_examples.py` | Validates example scripts run without errors |
| `test_sparse.py` | Sparse matrix implementation tests |
| `test_lpdot.py` | lpDot() function tests |
| `run_tests.py` | Test runner entry point |

---

## Code Conventions

### Naming Conventions

```python
# Classes: PascalCase
class LpVariable:
class LpProblem:
class PULP_CBC_CMD:

# Functions/Methods: snake_case (with some camelCase for legacy)
def lpSum(vector):          # Legacy convenience function
def lpDot(a, b):           # Legacy convenience function
def value(obj):            # Legacy convenience function
def to_dict():             # DEPRECATED (use toDict)
def toDict():              # New style

# Constants: UPPER_SNAKE_CASE
LpMinimize = 1
LpMaximize = -1
LpContinuous = "Continuous"
LpInteger = "Integer"
LpBinary = "Binary"

# Variable categories
LpStatusOptimal = 1
LpStatusInfeasible = -1
```

### Docstring Style

PuLP uses **mixed docstring styles** (Google-style and NumPy-style):

```python
def lpSum(vector):
    """
    Calculate the sum of a list of linear expressions.

    :param vector: A list of linear expressions
    :return: LpAffineExpression

    Example:
        >>> x = LpVariable("x")
        >>> y = LpVariable("y")
        >>> expr = lpSum([3*x, 2*y, 5])
    """
    ...
```

### Code Style

**Formatter**: Black (line length 88)

**Key Style Points**:
- 4-space indentation
- Single quotes for strings (Black's default)
- Type hints encouraged but not required (legacy codebase)
- Inline comments sparingly (prefer clear code)

### Import Organization

```python
# 1. Standard library
import os
import sys
from typing import Union, Optional

# 2. Third-party (if any)
import numpy as np

# 3. Local imports
from . import constants as const
from .pulp import LpVariable, LpProblem
from .utilities import lpSum, value
```

### File Conventions

**Python Version**: Target Python 3.7+ syntax (via pyupgrade)

**File Headers**: Include MIT license header in new files

**Deprecation**: Use `warnings.warn()` for deprecated features:
```python
import warnings

def to_dict(self):  # Deprecated method
    warnings.warn(
        "to_dict is deprecated, use toDict instead",
        category=DeprecationWarning,
        stacklevel=2
    )
    return self.toDict()
```

---

## Common Tasks

### Task 1: Add a New Solver

**Files to Modify**:
1. Create `pulp/apis/newsolver_api.py`
2. Import in `pulp/apis/__init__.py`
3. Add tests in `pulp/tests/test_pulp.py`
4. Document in `doc/source/technical/solvers.rst`

**Implementation Template**:
```python
# pulp/apis/newsolver_api.py
from .core import LpSolver_CMD, subprocess

class NEWSOLVER_CMD(LpSolver_CMD):
    name = "NEWSOLVER_CMD"

    def __init__(self, path=None, **kwargs):
        self.path = path or self.defaultPath()
        super().__init__(**kwargs)

    def defaultPath(self):
        return self.executableExtension("newsolver")

    def available(self):
        return self.executable(self.path)

    def actualSolve(self, lp):
        # Implementation here
        pass
```

**Add to `__init__.py`**:
```python
from .newsolver_api import NEWSOLVER_CMD
```

**Add Test Class**:
```python
class NEWSOLVER_CMDTest(BaseSolverTest.PuLPTest):
    solverClass = NEWSOLVER_CMD
```

### Task 2: Add a New Function to LpProblem

**File**: `pulp/pulp.py`

**Steps**:
1. Locate `class LpProblem` (around line 1000)
2. Add method with docstring
3. Add test in `test_pulp.py`
4. Update API docs if user-facing

**Example**:
```python
# In pulp/pulp.py, LpProblem class
def myNewMethod(self, param):
    """
    Description of what this method does.

    :param param: Parameter description
    :return: Return value description
    """
    # Implementation
    return result
```

### Task 3: Add a New Variable Type

**File**: `pulp/constants.py` and `pulp/pulp.py`

**Steps**:
1. Add constant to `constants.py`:
```python
LpNewType = "NewType"
LpCategories = {
    LpContinuous: "Continuous",
    LpInteger: "Integer",
    LpBinary: "Binary",
    LpNewType: "NewType",  # Add here
}
```

2. Update `LpVariable.__init__()` to handle new type
3. Update solver APIs to support new type
4. Add tests

### Task 4: Fix a Bug

**Workflow**:
1. Write a failing test in `test_pulp.py` that reproduces the bug
2. Run test to confirm it fails: `pytest -xvs test_pulp.py::TestClass::test_method`
3. Fix the bug in the appropriate module
4. Run test again to confirm fix
5. Run full test suite: `pulptest`
6. Format code: `black .`
7. Run pre-commit: `pre-commit run --all-files`
8. Commit with descriptive message

### Task 5: Add Documentation

**User Guide** (`doc/source/main/`):
- Add `.rst` file with tutorial content
- Include in `index.rst` toctree

**Case Study** (`doc/source/CaseStudies/`):
- Create `.rst` file with problem description
- Include full working code example
- Show output and interpretation

**API Reference** (`doc/source/technical/`):
- Usually auto-generated from docstrings
- Ensure class/function has good docstring
- Rebuild docs to verify: `cd doc && make html`

### Task 6: Update Dependencies

**File**: `pyproject.toml`

**Optional Dependencies** (solvers):
```toml
[project.optional-dependencies]
newsolver = ["newsolver-python-package"]
```

**Dev Dependencies**:
```toml
[dependency-groups]
dev = ["black", "mypy", "pytest", "sphinx", ...]
```

**Install Updated Deps**:
```bash
pip install -e .[newsolver]
pip install --group=dev .
```

---

## Important Gotchas

### 1. Variable Name Restrictions

**Issue**: Variable names must be valid LP format identifiers

**Rules**:
- Start with letter or underscore
- Only alphanumeric + underscore
- Avoid MPS/LP reserved words

**Validation**: `LpVariable.__init__()` checks and raises `PulpError`

```python
# Good
x = LpVariable("x1")
y = LpVariable("production_level")

# Bad (will raise error)
z = LpVariable("3rd_var")  # Starts with number
w = LpVariable("x-1")      # Contains hyphen
```

### 2. Binary Variables are Actually Integers

**Issue**: `LpBinary` is internally stored as `LpInteger` with bounds [0, 1]

```python
x = LpVariable("x", cat=LpBinary)
print(x.cat)  # "Integer" not "Binary"!
print(x.lowBound, x.upBound)  # 0, 1
```

**Implication**: Type checks should use `isBinary()` method, not `cat == LpBinary`

### 3. Expression Building Creates Copies

**Issue**: Expressions are immutable; operations create new objects

```python
expr = x + y
expr += z  # Creates NEW LpAffineExpression, doesn't modify in place

# Efficient pattern (especially in loops)
terms = [2*x, 3*y, 4*z]
expr = lpSum(terms)  # Better than chaining +=
```

### 4. Solver Availability vs. Functionality

**Issue**: `solver.available()` only checks if solver exists, not if it works

```python
solver = GUROBI()
if solver.available():  # Checks if gurobi binary/module exists
    # May still fail if no valid license
    prob.solve(solver)
```

**Best Practice**: Wrap solve calls in try-except for `PulpSolverError`

### 5. Temporary File Cleanup

**Issue**: Command-line solvers create temp files that may persist on error

**Debugging**: Set `keepFiles=True` to inspect solver input/output files

```python
solver = PULP_CBC_CMD(keepFiles=True)  # Files remain in /tmp or OS temp dir
prob.solve(solver)
# Inspect tmpXXXX.lp and tmpXXXX.sol files
```

### 6. Objective Must Be Added First

**Issue**: The first expression added to `LpProblem` becomes the objective

```python
prob = LpProblem("test", LpMinimize)

# WRONG: This becomes the objective!
prob += x + y <= 10  # Constraint treated as objective

# CORRECT:
prob += 2*x + 3*y      # Objective (no sense operator)
prob += x + y <= 10    # Constraint
```

**Safe Pattern**: Always set objective explicitly:
```python
prob.setObjective(2*x + 3*y)
prob += x + y <= 10
```

### 7. Variable Bounds vs. Constraints

**Performance**: Use variable bounds instead of constraints when possible

```python
# Less efficient
x = LpVariable("x")
prob += x >= 0
prob += x <= 10

# More efficient (solver handles bounds specially)
x = LpVariable("x", lowBound=0, upBound=10)
```

### 8. lpSum() vs. sum()

**Issue**: Use `lpSum()` for better performance on large lists

```python
# Slow (creates many intermediate objects)
expr = sum([coef*var for coef, var in zip(coeffs, vars)])

# Fast (optimized for linear expressions)
expr = lpSum([coef*var for coef, var in zip(coeffs, vars)])

# Alternative (even better for large problems)
expr = lpDot(coeffs, vars)
```

### 9. MPS Format Limitations

**Issue**: MPS format has strict naming rules (8-char limit in some variants)

**Truncation**: Long variable/constraint names may be truncated

**Debugging**: Use `writeLP()` instead for human-readable format:
```python
prob.writeLP("problem.lp")    # Easier to read
prob.writeMPS("problem.mps")  # Standard format
```

### 10. Status Codes Are Not Booleans

**Issue**: Don't use `if status:` to check success

```python
status = prob.solve()

# WRONG
if status:  # LpStatusInfeasible = -1 is truthy!
    print("Optimal")

# CORRECT
if status == LpStatusOptimal:
    print("Optimal")

# Or use string representation
if LpStatus[status] == "Optimal":
    print("Optimal")
```

### 11. Warm Start Requirements

**Issue**: Warm starts require solver support and previous solution

```python
# First solve
prob.solve(solver)

# Modify problem slightly
prob += new_constraint

# Warm start (uses previous solution)
prob.solve(solver, warmStart=True)
# Only works if:
# 1. Solver supports warm starts
# 2. prob.solverModel exists from previous solve
# 3. Variable set hasn't changed
```

### 12. Thread Safety

**Issue**: PuLP is NOT thread-safe for sharing problems

**Safe Pattern**: Create separate `LpProblem` instances per thread

```python
# WRONG
def solve_thread(prob):
    prob.solve()

threads = [Thread(target=solve_thread, args=(prob,)) for _ in range(10)]

# CORRECT
def solve_thread(params):
    prob = create_problem(params)  # New instance per thread
    prob.solve()

threads = [Thread(target=solve_thread, args=(p,)) for p in params]
```

---

## Contributing to PuLP

### Contributor License Agreement (CLA)

**Required**: All contributors must sign the COIN-OR CLA via cla-assistant

**Process**: Automatic prompt on first PR submission

**Link**: https://cla-assistant.io/coin-or/pulp

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows Black formatting (`black .`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Tests added for new functionality (`test_pulp.py`)
- [ ] All tests pass (`pulptest`)
- [ ] Docstrings added for public methods/classes
- [ ] Documentation updated if user-facing changes
- [ ] Issue reference in PR description

### Commit Message Format

**Style**: Descriptive, imperative mood

**Good Examples**:
```
Add HiGHS solver support via highspy module
Fix variable name validation for Unicode characters
Update documentation for solver configuration
```

**Bad Examples**:
```
Fixed stuff
Updates
WIP
```

### Branch Workflow

1. Fork repository to your GitHub account
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit
4. Push to your fork: `git push origin feature/my-feature`
5. Open PR against `coin-or/pulp:master`

### Code Review Process

1. Automated checks run (tests, formatting)
2. Maintainers review code
3. Address review feedback
4. Maintainer merges when approved

---

## Additional Resources

### Official Documentation
- **Main Docs**: https://coin-or.github.io/pulp/
- **GitHub**: https://github.com/coin-or/pulp
- **PyPI**: https://pypi.org/project/PuLP/

### Getting Help
- **Discussions**: https://github.com/coin-or/pulp/discussions
- **Issues**: https://github.com/coin-or/pulp/issues
- **COIN-OR**: https://www.coin-or.org/

### Related Projects
- **Amply**: Data file parser for AMPL
- **lparray**: NumPy-like arrays for LP
- **ORLoge**: Logging for optimization
- **Pytups**: Tuple-based data structures for OR

---

## Quick Reference

### Key Files by Task

| Task | Files to Check |
|------|----------------|
| Add new solver | `pulp/apis/newsolver_api.py`, `pulp/apis/__init__.py` |
| Modify core modeling | `pulp/pulp.py` (LpVariable, LpProblem, LpConstraint) |
| Add utility function | `pulp/utilities.py` |
| Add constants | `pulp/constants.py` |
| Fix format issues | `pulp/mps_lp.py` |
| Add tests | `pulp/tests/test_pulp.py` |
| Update docs | `doc/source/**/*.rst` |
| Configure build | `pyproject.toml` |

### Essential Commands

```bash
# Development
pip install -e .
pip install --group=dev .

# Testing
pulptest
pytest pulp/tests/test_pulp.py -xvs

# Code Quality
black .
mypy pulp/
pre-commit run --all-files

# Documentation
cd doc && make html

# Building
python -m build
```

### Common Code Patterns

```python
# Create variable
x = LpVariable("x", lowBound=0, cat=LpContinuous)

# Create problem
prob = LpProblem("MyProblem", LpMinimize)

# Add objective
prob += lpSum([c*x for c, x in zip(costs, vars)])

# Add constraint
prob += lpSum([a*x for a, x in zip(coeffs, vars)]) <= rhs

# Solve
status = prob.solve(PULP_CBC_CMD(msg=False))

# Check result
if status == LpStatusOptimal:
    solution = {v.name: value(v) for v in prob.variables()}
```

---

**Document Maintenance**: Update this file when:
- Major architectural changes occur
- New conventions are adopted
- Development workflow changes
- Common patterns emerge from issues/PRs

**Questions?** Open an issue or discussion on GitHub.
