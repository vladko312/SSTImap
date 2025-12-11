# Shared closures
close_single_quotes = [("1'", "'1")]
close_double_quotes = [('1"', '"1')]
close_backticks = [('1`', '`1')]
close_single_double_quotes = close_single_quotes + close_double_quotes
integer = [('1', '1')]
float = [('1.0', '1.0')]
string = [('"1"', '"1"')]
close_dict = [('}', '{"1":'), (':1}', '{')]
close_function = [(')', '(')]
close_list = [(']', '[')]
empty = [('', '')]
close_triple_quotes = [('1"""', '"""1'), ("1'''", "'''1")]

# Python triple quotes and if and for loop termination.
if_loops = [(':', '')]
int_to_float = [('1.0', '1')]

# Javascript needs this to bypass assignations
var = [('a', '')]

# Java needs booleans to bypass conditions and iterable objects
true_var = [('true', 'true')]
iterable_var = [('[1]', '')]
