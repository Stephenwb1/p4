import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method(name, rule):
    def method(state, ID):
        # Check if the item is already available
        produced_items = rule.get('Produces', {})
        for item, qty in produced_items.items():
            if getattr(state, item)[ID] >= qty:
                return []
        
        # Check if requirements are met
        required_items = rule.get('Requires', {})
        for tool, count in required_items.items():
            if getattr(state, tool)[ID] < count:
                return False 
        
        # Create the list of tasks
        tasks = []
        produces = rule.get('Produces', {})
        for produced_item, count in produces.items():
            tasks.append((f'produce_{produced_item}', ID))
        
        consumes = rule.get('Consumes', {})
        for item, count in consumes.items():
            tasks.append((f'consume_{item}', ID, count))
        
        return tasks
	

    method.__name__ = name
    return method

def declare_methods(data):
    recipes = data['Recipes']
	
    item_to_recipe = {}
    for name, rule in recipes.items():
        produces = rule.get('Produces', {})
        for item in produces.keys():
            item_to_recipe[item] = rule

    methods = {}
    for item, rule in item_to_recipe.items():
        method_name = f'produce_{item}'
        if method_name not in methods:
            methods[method_name] = make_method(method_name, rule)
    
    for method_name, method in methods.items():
        pyhop.declare_methods(method_name, method)	

def make_operator (name, rule):
	def operator (state, ID):
		for req, qty in rule.get('Requires', {}).items():
			if getattr(state, req)[ID] < qty:
				return False
		
		for req, qty in rule.get('Consumes', {}).items():
			setattr(state, req, {ID: getattr(state, req)[ID] - qty})
		
		for prod, qty in rule.get('Produces', {}).items():
			setattr(state, prod, {ID: getattr(state, prod)[ID] + qty})
		
		state.time[ID] += rule['Time']

		return state
	operator.__name__ = name
	return operator

def declare_operators (data):
	# your code here
	# hint: call make_operator, then declare the operator to pyhop using pyhop.declare_operators(o1, o2, ..., ok)
	
	operators = []

	for recipe, rule in data['Recipes'].items():
		operators.append(make_operator(recipe, rule))

	pyhop.declare_operators(*operators)

def add_heuristic (data, ID):
	# prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
	def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
		# your code here
		return False # if True, prune this branch

	pyhop.add_check(heuristic)


def set_up_state (data, ID, time=0):
	state = pyhop.State('state')
	state.time = {ID: time}

	for item in data['Items']:
		setattr(state, item, {ID: 0})

	for item in data['Tools']:
		setattr(state, item, {ID: 0})

	for item, num in data['Initial'].items():
		setattr(state, item, {ID: num})

	return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=239) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	pyhop.print_operators()
	pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
