How to save and load models in PuLP
==========================================

Saving a model can be useful when the building time takes too long, when the model needs to be passed to another computer to solve, or a problem needs to be shared.
PuLP offers three ways to export a model: to an MPS file, a JSON file, or an LP file. Each offers advantages over the other.

1. **MPS format** is an industry standard. But it is not very flexible so some information cannot be stored. It stores only variables and constraints. It does not store the values of variables. resource: https://lpsolve.sourceforge.net/5.5/mps-format.htm https://en.wikipedia.org/wiki/MPS_(format)

2. **JSON format** is made to fit how pulp stores the information and so it does not lose information: this format file saves enough data to be able to restore a complete pulp model on reading it.

3. **LP format** is a human-readable text format that represents the linear programming model. It is not possible to load LP files back into PuLP models.

The interface to import and export for all three formats is similar as can be seen in the Examples 1, 2 and 3 below.

PuLP does not support saving and loading models in other formats such as `XMIP` or `NL https://web.archive.org/web/20161228202832/https://cfwebprod.sandia.gov/cfdocs/CompResearch/docs/nlwrite20051130.pdf`.

Considerations
------------------

The following considerations need to be taken into account:

======  ======== ========  ================= =================== ======================
Format  Can Read Can Write  Stores Solution  human-readable      Stores Ints and Bools 
======  ======== ========  ================= =================== ======================
MPS     Yes      Yes        No               No                  No
LP      No       Yes        No               Yes                 No
JSON    Yes      Yes        Yes              Yes                 Yes
======  ======== ========  ================= =================== ======================


Further more:

#. Variable names need to be unique. PuLP permits having variable names because it uses an internal code for each one. But we do not export that code. So we identify variables by their name only.
#. Variables are not exported in a grouped way. This means that if you have several `dictionaries of many variables each` you will end up with a very long list of variables. This can be seen in the Example 2.
#. Output information is also written to the JSON format. This means that the status, solution status, the values of variables and shadow prices / reduced costs are exported too. This means that it is possible to export a model that has been solved and then read it again only to see the values of the variables.
#. For JSON, we use the base `json` package. But if `ujson` is available, we use that so the import / export can be really fast.

Example 1: JSON
----------------

A very simple example taken from the internal tests. Imagine the following problem::

    from pulp import *

    prob = LpProblem("test_export_dict_MIP", LpMinimize)
    x = LpVariable("x", 0, 4)
    y = LpVariable("y", -1, 1)
    z = LpVariable("z", 0, None, LpInteger)
    prob += x + 4 * y + 9 * z, "obj"
    prob += x + y <= 5, "c1"
    prob += x + z >= 10, "c2"
    prob += -y + z == 7.5, "c3"

We can now export the problem into a dictionary::

    data = prob.to_dict()

We now have a dictionary with a lot of data::

    {'constraints': [{'coefficients': [{'name': 'x', 'value': 1},
                                       {'name': 'y', 'value': 1}],
                      'constant': -5,
                      'name': 'c1',
                      'pi': None,
                      'sense': -1},
                     {'coefficients': [{'name': 'x', 'value': 1},
                                       {'name': 'z', 'value': 1}],
                      'constant': -10,
                      'name': 'c2',
                      'pi': None,
                      'sense': 1},
                     {'coefficients': [{'name': 'y', 'value': -1},
                                       {'name': 'z', 'value': 1}],
                      'constant': -7.5,
                      'name': 'c3',
                      'pi': None,
                      'sense': 0}],
     'objective': {'coefficients': [{'name': 'x', 'value': 1},
                                    {'name': 'y', 'value': 4},
                                    {'name': 'z', 'value': 9}],
                   'name': 'obj'},
     'parameters': {'name': 'test_export_dict_MIP',
                    'sense': 1,
                    'sol_status': 0,
                    'status': 0},
     'sos1': {},
     'sos2': {},
     'variables': [{'cat': 'Continuous',
                    'dj': None,
                    'lowBound': 0,
                    'name': 'x',
                    'upBound': 4,
                    'varValue': None},
                   {'cat': 'Continuous',
                    'dj': None,
                    'lowBound': -1,
                    'name': 'y',
                    'upBound': 1,
                    'varValue': None},
                   {'cat': 'Integer',
                    'dj': None,
                    'lowBound': 0,
                    'name': 'z',
                    'upBound': None,
                    'varValue': None}]}

We can now import this dictionary::

    var1, prob1 = LpProblem.from_dict(data)
    var1
    # {'x': x, 'y': y, 'z': z}
    prob1
    # test_export_dict_MIP:
    # MINIMIZE
    # 1*x + 4*y + 9*z + 0
    # SUBJECT TO
    # c1: x + y <= 5
    # c2: x + z >= 10
    # c3: - y + z = 7.5
    # VARIABLES
    # x <= 4 Continuous
    # -1 <= y <= 1 Continuous
    # 0 <= z Integer

As you can see we get a tuple with size 2 with: (1) a variables dictionary and (2) a PuLP model object. We can now solve that problem::

    prob1.solve()

And the result will be available in our *new* variables::

    var1['x'].value()
    # 3.0


Example 2: MPS
----------------

The same model::

    from pulp import *
    prob = LpProblem("test_export_dict_MIP", LpMinimize)
    x = LpVariable("x", 0, 4)
    y = LpVariable("y", -1, 1)
    z = LpVariable("z", 0, None, LpInteger)
    prob += x + 4 * y + 9 * z, "obj"
    prob += x + y <= 5, "c1"
    prob += x + z >= 10, "c2"
    prob += -y + z == 7.5, "c3"

We can now export the problem into an MPS file::

    prob.writeMPS("test.mps")

We can now import this file::

    var1, prob1 = LpProblem.fromMPS("test.mps")
    var1
    # {'x': x, 'y': y, 'z': z}
    prob1
    # test_export_dict_MIP:
    # MINIMIZE
    # 1*x + 4*y + 9*z + 0
    # SUBJECT TO
    # c1: x + y <= 5
    # c2: x + z >= 10
    # c3: - y + z = 7.5
    # VARIABLES
    # x <= 4 Continuous
    # -1 <= y <= 1 Continuous
    # 0 <= z Integer

The resulting tuple is exactly the same format as the previous one.

Example 3: LP
----------------

The same model::

    from pulp import *
    prob = LpProblem("test_export_dict_MIP", LpMinimize)
    x = LpVariable("x", 0, 4)
    y = LpVariable("y", -1, 1)
    z = LpVariable("z", 0, None, LpInteger)
    prob += x + 4 * y + 9 * z, "obj"
    prob += x + y <= 5, "c1"
    prob += x + z >= 10, "c2"
    prob += -y + z == 7.5, "c3"

We can now export the problem into an LP file::

    prob.writeLP("test.lp")

This generates the following output file `test.lp`::

    \* test_export_dict_MIP *\
    Minimize
    obj: x + 4 y + 9 z
    Subject To
    c1: x + y <= 5
    c2: x + z >= 10
    c3: - y + z = 7.5
    Bounds
    x <= 4
    -1 <= y <= 1
    0 <= z
    Generals
    z
    End

But we **cannot** read LP files back into PuLP models.

Example 4: JSON
------------------

Here we explore a more complicated example using the model in :ref:`set-partitioning-problem`::

    import pulp

    max_tables = 5
    max_table_size = 4
    guests = 'A B C D E F G I J K L M N O P Q R'.split()

    def happiness(table):
        """
        Find the happiness of the table
        - by calculating the maximum distance between the letters
        """
        return abs(ord(table[0]) - ord(table[-1]))
                    
    # create list of all possible tables
    possible_tables = [tuple(c) for c in pulp.allcombinations(guests, 
                                            max_table_size)]

    # create a binary variable to state that a table setting is used
    x = pulp.LpVariable.dicts('table', possible_tables, 
                                lowBound = 0,
                                upBound = 1,
                                cat = pulp.LpInteger)

    seating_model = pulp.LpProblem("Wedding_Seating_Model", pulp.LpMinimize)

    seating_model += pulp.lpSum([happiness(table) * x[table] for table in possible_tables])

    # specify the maximum number of tables
    seating_model += pulp.lpSum([x[table] for table in possible_tables]) <= max_tables, \
                                "Maximum_number_of_tables"

    # A guest must seated at one and only one table
    for guest in guests:
        seating_model += pulp.lpSum([x[table] for table in possible_tables
                                    if guest in table]) == 1, "Must_seat_%s"%guest

We *could* directly solve the model doing::

    seating_model.solve()

Instead, we are going to export it to a JSON file::

    seating_model.to_json("seating_model.json")

And re-import it::

    wedding_vars, wedding_model = LpProblem.from_json("seating_model.json")

We inspect the variables::

    wedding_vars
    {"table_('A',)": table_('A',), "table_('A',_'B')": table_('A',_'B'), "table_('A',_'B',_'C')": table_('A',_'B',_'C'), "table_('A',_'B',_'C',_'D')": table_('A',_'B',_'C',_'D'), "table_('A',_'B',_'C',_'E')": table_('A',_'B',_'C',_'E'), ...}

As can be seen, it is no longer a dictionary indexed by the original tuples. Unfortunately, it has become a flat dictionary with concatenated names.

We can still solve the model, though::

    wedding_model.solve()

And inspect some of the values::

    wedding_vars["table_('M',_'N')"].value()
    # 1.0


Grouping variables
-------------------

As the "Considerations" section mentions, the grouping of variables is not restored automatically. Nevertheless, by using some strict naming convention on variable names and clever parsing, one can reconstruct the original structure of the variables.

Caveats with JSON and pandas / numpy data types
--------------------------------------------------

The `json` module in python has some issues transforming numpy data types (e.g., `np.integer`). The easier way to solve this problem is to provide a custom encoding class as shown `here <https://stackoverflow.com/a/57915246/6508131>`_::

    import numpy as np
    #(...)
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return super(NpEncoder, self).default(obj)

    wedding_model.to_json("seating_model.json", cls=NpEncoder)

Note: this custom encoding class may not work with the `ujson` package. An alternative is to cast all values using `int()` or `float()` before using them in `pulp`.
