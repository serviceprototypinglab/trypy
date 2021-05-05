import sys
import contextlib
import io
import random
import datetime
import os
import time

import math

DEFAULTPORT = 8080
DEFAULTRING = 91

# Telnet line break compliance
def nprint(*args, **kwargs):
    if not "end" in kwargs or kwargs["end"] == "\n":
        kwargs["end"] = "\r\n"
    oprint(" ".join(map(str, args)), **kwargs)
oprint = print
print = nprint

"""
def ninput(s):
    return oinput(s)
oinput = input
input = ninput
"""

class VariableCheck:
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value

    def check(self, space, s):
        if "__builtins__" in space:
            space.pop("__builtins__")
        good = True
        if self.name:
            good = False
            if self.name in space:
                good = True
        if good and self.value is not None:
            good = False
            for var in space.copy():
                val = eval(var, space)
                if val == self.value:
                    good = var
                    break
        if good:
            return good
        return False

    def resolve(self, space):
        if type(self.name) == str:
            self.name = eval(self.name)
        if type(self.value) == str:
            self.value = eval(self.value)

class OutputCheck:
    def __init__(self, result):
        self.result = result

    def check(self, space, s):
        try:
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                eval(s, space)
            ret = f.getvalue().strip()
            if ret == self.result:
                return True
            return False
        except:
            return False

class ValueCheck:
    def __init__(self, value):
        self.value = value

    def check(self, space, s):
        safemods = ("math",)
        if "." in s:
            potmod = s[:s.index(".")]
            if potmod.isalpha():
                if potmod in safemods:
                    import importlib
                    mod = importlib.import_module(potmod)
                    space[potmod] = mod
        try:
            ret = eval(s, space)
        except:
            return False
        if ret == self.value:
            return True
        return False

class FuncCheck:
    def __init__(self, arg, result):
        self.arg = arg
        self.result = result

    def check(self, space, s):
        try:
            f = eval(s, space)
        except:
            return False
        try:
            ret = f(self.arg)
        except:
            return False
        else:
            if ret == self.result:
                return True
        return False

class ExCheck:
    def __init__(self):
        pass

    def check(self, space, s):
        try:
            exec(s)
        except:
            return True
        return False

class AstCheck:
    def __init__(self, ops, result):
        self.ops = ops
        self.result = result

    def check(self, space, s):
        try:
            f = eval(s, space)
        except:
            return False
        if f == self.result:
            ops = 0
            dops = 0
            for op in ("+", "-", "*", "/", "//", "%", "**"):
                num = s.count(op)
                if num:
                    ops += 1
                    if op in ("//", "**"):
                        dops += 1
            ops -= dops
            if ops == self.ops:
                return True
        return False

class Goal:
    def __init__(self, text, preexec, check, metavar=None, resolve=False):
        self.text = text
        self.preexec = preexec
        self.check = check
        self.metavar = metavar
        self.resolve = resolve

def check(c, meta, space, s):
    m = c.check(space, s)
    if m:
        if meta:
            space["__" + meta] = m
        return True
    else:
        return False

def process(goals, banner=True):
    space = {}
    hints = 4

    if banner:
        print("Welcome to TryPy! You must achieve all goals with valid Python syntax.")
        print(f"There are {len(goals)} goals.")

    for idx, goal in enumerate(goals):
        if len(goals) > 2:
            if idx == len(goals) // 2:
                print("Well done - half of goals achieved!")
            if idx == len(goals) - 1:
                print("Very well done - last goal!")

        if "__builtins__" in space:
            space.pop("__builtins__")
        print()
        print("== Next Goal ==")
        rnd = random.randrange(5)
        if rnd == 0:
            print("Having fun?")
        elif rnd == 1:
            print("Now try your luck:")
        print(goal.text.format(**space))
        if goal.resolve:
            goal.check.resolve(space)

        while True:
            try:
                s = input(":)>>> ")
            except Exception:
                print("Okthxbye.")
                return False
            except KeyboardInterrupt:
                print("Okthxbye.")
                return False
            if not s:
                continue
            if s == "?":
                print(goal.text.format(**space))
                continue
            if "import" in s or "open" in s or ";" in s:
                print("Unbreakable game.")
                continue
            print("Evaluating", end="")
            for i in range(3):
                time.sleep(0.2)
                print(".", end="")
                sys.stdout.flush()
            print()
            try:
                if goal.preexec:
                    exec(s, space)
            except Exception as e:
                print("Error:", e)
            except SystemExit:
                print("Okthxbye.")
                return False
            else:
                if check(goal.check, goal.metavar, space, s):
                    print("Good!")
                    break
                else:
                    try:
                        out = space[s]
                    except:
                        try:
                            out = eval(s, space)
                        except Exception as e:
                            print("Error:", e)
                        except SystemExit:
                            print("Okthxbye.")
                            return False
                        else:
                            print("Well, not quite.")
                    else:
                        print(f"You are not quite concentrating on your job in achieving goals. {hints} hints left.")
                        if hints > 0:
                            hints -= 1
                            print(out)
                        else:
                            print("Not showing anything.")

    return True

def application():
    g1 = Goal("Create a variable 'a' by assignment.", True, VariableCheck(name="a"))
    g2 = Goal("Create a variable with numeric value 123.", True, VariableCheck(value=123), metavar="z")
    g3 = Goal("Give the instruction to precisely output the character sequence shown between bars, without the bars themselves: |* * *|.", False, OutputCheck("* * *"))
    g4 = Goal("Double the value of variable '{__z}'.", True, VariableCheck(name="space['__z']", value="space[space['__z']] * 2"), resolve=True)
    g5 = Goal("Provoke an exception.", False, ExCheck())
    g6 = Goal("Transform variable '{__z}' into a list whose only value is the current scalar value of the variable.", True, VariableCheck(name="space['__z']", value="[space[space['__z']]]"), resolve=True)
    g7 = Goal("Calculate the result of the boolean expression 'True and not True'.", False, ValueCheck(False))
    g8 = Goal("Type a string literal containing (nothing but) a pair of double quotes.", False, ValueCheck("\"\""))
    g9 = Goal("Give the name of the function, without parentheses or arguments, to determine the maximum value of a list of values.", False, FuncCheck(arg=[1, 3, 9], result=9))
    g10 = Goal("Create a variable with empty dictionary value.", True, VariableCheck(value={}), metavar="dic")
    g11 = Goal("Update the dictionary '{__dic}' to contain key 'k' with value 'v'.", True, VariableCheck(name="space['__dic']", value={"k": "v"}), resolve=True)
    g12 = Goal("Generate the list, with actual list datatype: [1, 3, 5, ... 99]", False, ValueCheck(list(range(1, 100, 2))))
    g13 = Goal("Type an expression yielding the result 13 by combining exactly 3 distinct arithmetic operators.", False, AstCheck(3, 13))
    g14 = Goal("Calculate the cosine value of 5 (hint: necessary modules can be assumed to be already imported).", False, ValueCheck(math.cos(5)))

    tstart = time.time()

    ret = process([g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14])

    if ret:
        print()
        print("/ " * 20)
        print("You have reached the boss level. Prepare for the final goal!")

        gboss = Goal("Enter an unary Lambda function definition that negates its (numeric) argument.", False, FuncCheck(arg=3, result=-3))

        ret = process([gboss], banner=False)

    if ret:
        print("Wonderful - you did the final goal!")
        tsec = int(time.time() - tstart)
        day = datetime.datetime.now().day
        port = os.getenv("PORT")
        if not port:
            port = DEFAULTPORT
        else:
            port = int(port)
        ring = os.getenv("RING")
        if not ring:
            ring = DEFAULTRING
        else:
            ring = int(ring)
        magic = day * port % ring + tsec % ring
        print("----- 8< -----")
        print("You took", tsec, "seconds to play.")
        print("The magic number is:", magic)
        print("----- 8< -----")

        input("Inform these two numbers to your lecturer, and then press enter to quit...")

if __name__ == "__main__":
    application()
