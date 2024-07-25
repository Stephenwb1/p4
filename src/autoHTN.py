import pyhop
import json

def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num:
        return []
    return False

def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods('have_enough', check_enough, produce_enough)

def produce(state, ID, item):
    return [('produce_{}'.format(item), ID)]

pyhop.declare_methods('produce', produce)

def make_method(name, rule):
    def method(state, ID):
        tasks = []
        for req, qty in rule.get('Requires', {}).items():
            tasks.append(('have_enough', ID, req, qty))
        for cons, qty in rule.get('Consumes', {}).items():
            tasks.append(('have_enough', ID, cons, qty))
        tasks.append((f'op_{name.replace(" ", "_")}', ID))
        return tasks
    return method

def declare_methods(data):
    methods_dict = {}
    for recipe, rule in data['Recipes'].items():
        produced_item = list(rule['Produces'].keys())[0]
        if produced_item not in methods_dict:
            methods_dict[produced_item] = []
        methods_dict[produced_item].append((recipe, make_method(recipe, rule)))

    for item, methods in methods_dict.items():
        # Sort methods by the time required for their corresponding rules
        sorted_methods = sorted(methods, key=lambda x: data['Recipes'][x[0]]['Time'])
        pyhop.declare_methods(f'produce_{item}', *[m[1] for m in sorted_methods])

def make_operator(rule):
    def operator(state, ID):
        for req, qty in rule.get('Requires', {}).items():
            if getattr(state, req)[ID] < qty:
                return False
        
        for cons, qty in rule.get('Consumes', {}).items():
            setattr(state, cons, {ID: getattr(state, cons)[ID] - qty})
        
        for prod, qty in rule.get('Produces', {}).items():
            setattr(state, prod, {ID: getattr(state, prod)[ID] + qty})
        
        state.time[ID] -= rule['Time']
        return state
    return operator

def declare_operators(data):
    operators = [make_operator(rule) for recipe, rule in data['Recipes'].items()]
    pyhop.declare_operators(*operators)

def add_heuristic(data, ID):
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # Prevent infinite loops by limiting recursive calls and redundant tasks
        if curr_task in plan:
            return True
        if len(calling_stack) > 1 and curr_task == calling_stack[-2]:
            return True
        if depth > 50:  # Reduce depth limit to prevent deep recursion
            return True
        return False
    pyhop.add_check(heuristic)

def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items']:
        setattr(state, item, {ID: 0})

    for item in data['Tools']:
        setattr(state, item, {ID: 0})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state

def set_up_goals(data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))
    return goals

# Define the op_punch_for_wood operator
def op_punch_for_wood(state, ID):
    if state.time[ID] >= 4:
        state.wood[ID] += 1
        state.time[ID] -= 4
        return state
    return False

if __name__ == '__main__':
    rules_filename = 'crafting.json'

    with open(rules_filename) as f:
        data = json.load(f)

    state = set_up_state(data, 'agent', time=239)
    goals = set_up_goals(data, 'agent')

    declare_operators(data)
    declare_methods(data)
    add_heuristic(data, 'agent')

    # Declare the op_punch_for_wood operator
    pyhop.declare_operators(op_punch_for_wood)

    # Print declared operators and methods for debugging
    pyhop.print_operators()
    pyhop.print_methods()

    pyhop.pyhop(state, goals, verbose=3)
