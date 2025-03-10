import os
from functions.basefun import BaseFunction
from utils.errors import RTError
from execution.runtime import RTResult
from core.values import List, Number, String
from core.interpreter import Interpreter
from core.lexer import Lexer
from core.parser import Parser
from core.values import Context, Number, SymbolTable


def run(fn, text):
    # Generate tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error

    # Run program
    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error


class BuiltInFunction(BaseFunction):
    """Represents a built-in function in the runtime."""

    def __init__(self, name):
        """Initialize a new BuiltInFunction with the given name."""
        super().__init__(name)

    def execute(self, args):
        """Execute the built-in function with the provided arguments.

        This method:
          1. Generates a new execution context.
          2. Dynamically selects the specific execute method (e.g., execute_print) based on the function name.
          3. Checks that the correct number of arguments is provided.
          4. Calls the specific built-in function implementation and returns its result.
        """
        res = RTResult()
        exec_ctx = self.generate_new_context()

        method_name = f"execute_{self.name}"
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
        if res.should_return():
            return res

        return_value = res.register(method(exec_ctx))
        if res.should_return():
            return res
        return res.success(return_value)

    def no_visit_method(self, node, context):
        """Handle the case where no execute method is defined for this built-in function."""
        raise Exception(f"No execute_{self.name} method defined")

    def copy(self):
        """Create a copy of this built-in function."""
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        """Return the string representation of the built-in function."""
        return f"<built-in function {self.name}>"

    #####################################

    def execute_print(self, exec_ctx):
        """Built-in function to print a value to the console."""
        print(str(exec_ctx.symbol_table.get("value")))
        return RTResult().success(Number.null)

    execute_print.arg_names = ["value"]

    def execute_print_ret(self, exec_ctx):
        """Built-in function to return a printed value as a string.

        Retrieves the value associated with the key "value" and returns it as a String.
        """
        return RTResult().success(String(str(exec_ctx.symbol_table.get("value"))))

    execute_print_ret.arg_names = ["value"]

    def execute_input(self, exec_ctx):
        """Built-in function to take input from the user."""
        text = input()
        return RTResult().success(String(text))

    execute_input.arg_names = []

    def execute_input_int(self, exec_ctx):
        """Built-in function to take integer input from the user."""
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult().success(Number(number))

    execute_input_int.arg_names = []

    def execute_clear(self, exec_ctx):
        """Built-in function to clear the console."""
        os.system("cls" if os.name == "nt" else "cls")
        return RTResult().success(Number.null)

    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        """Built-in function to check if a value is a Number."""
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult().success(Number.true if is_number else Number.false)

    execute_is_number.arg_names = ["value"]

    def execute_is_string(self, exec_ctx):
        """Built-in function to check if a value is a String."""
        is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult().success(Number.true if is_number else Number.false)

    execute_is_string.arg_names = ["value"]

    def execute_is_list(self, exec_ctx):
        """Built-in function to check if a value is a List."""
        is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
        return RTResult().success(Number.true if is_number else Number.false)

    execute_is_list.arg_names = ["value"]

    def execute_is_function(self, exec_ctx):
        """Built-in function to check if a value is a function."""
        is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult().success(Number.true if is_number else Number.false)

    execute_is_function.arg_names = ["value"]

    def execute_append(self, exec_ctx):
        """Built-in function to append a value to a list."""
        list_ = exec_ctx.symbol_table.get("list")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be list",
                    exec_ctx,
                )
            )

        list_.elements.append(value)
        return RTResult().success(Number.null)

    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, exec_ctx):
        """Built-in function to pop an element from a list."""
        list_ = exec_ctx.symbol_table.get("list")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(list_, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be list",
                    exec_ctx,
                )
            )

        if not isinstance(index, Number):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be number",
                    exec_ctx,
                )
            )

        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Element at this index could not be removed from list because index is out of bounds",
                    exec_ctx,
                )
            )
        return RTResult().success(element)

    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, exec_ctx):
        """Built-in function to extend one list with another."""
        listA = exec_ctx.symbol_table.get("listA")
        listB = exec_ctx.symbol_table.get("listB")

        if not isinstance(listA, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "First argument must be list",
                    exec_ctx,
                )
            )

        if not isinstance(listB, List):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be list",
                    exec_ctx,
                )
            )

        listA.elements.extend(listB.elements)
        return RTResult().success(Number.null)

    execute_extend.arg_names = ["listA", "listB"]

    def execute_len(self, exec_ctx):
        """Built-in function to obtain the length of a list or string."""
        list_ = exec_ctx.symbol_table.get("list")

        if not isinstance(list_, List) and not isinstance(list_, String):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Argument must be list or string",
                    exec_ctx,
                )
            )

        if isinstance(list_, List):
            return RTResult().success(Number(len(list_.elements)))

        return RTResult().success(Number(len(list_.value)))

    execute_len.arg_names = ["list"]

    def execute_run(self, exec_ctx):
        """Built-in function to run a script from a file."""
        fn = exec_ctx.symbol_table.get("fn")

        if not isinstance(fn, String):
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Second argument must be string",
                    exec_ctx,
                )
            )

        fn = fn.value

        try:
            with open(fn, "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f'Failed to load script "{fn}"\n' + str(e),
                    exec_ctx,
                )
            )

        _, error = run(fn, script)

        if error:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f'Failed to finish executing script "{fn}"\n' + error.as_string(),
                    exec_ctx,
                )
            )

        return RTResult().success(Number.null)

    execute_run.arg_names = ["fn"]


BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_number = BuiltInFunction("is_number")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")
BuiltInFunction.len = BuiltInFunction("len")
BuiltInFunction.run = BuiltInFunction("run")


global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("MATH_PI", Number.math_PI)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
global_symbol_table.set("RUN", BuiltInFunction.run)
