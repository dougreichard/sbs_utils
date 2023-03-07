from asyncio.log import logger
from enum import IntEnum, Enum
import re
import ast
import os
from .. import fs
from zipfile import ZipFile
from .. import faces, scatter
import math
import itertools
import logging
import random
from io import StringIO


# tokens
#
# Optional color:
#       (\s+color\s*["'](?P<color>[ \t\S]+)["'])?
# name tag
#       (?P<name>\w+)
# Conditional
#       (\s+if(?P<if>.+))?
#
LIST_REGEX = r"""(\[[\s\S]+?\])"""
DICT_REGEX = r"""(\{[\s\S]+?\})"""
PY_EXP_REGEX = r"""((?P<py>~~)[\s\S]+?(?P=py))"""
STRING_REGEX = r"""((?P<quote>((["']{3})|["']))[ \t\S]*(?P=quote))"""

OPT_COLOR = r"""(\s*color\s*["'](?P<color>[ \t\S]+)["'])?"""
IF_EXP_REGEX = r"""(\s+if(?P<if_exp>.+))?"""
BLOCK_START = r":[ |\t]*(?=\r\n|\n|\#)"


class MastCompilerError:
    def __init__(self, message, line_no):
        if isinstance(message, str):
            self.messages = [message]
        else:
            self.messages = message
        self.line_no = line_no


class ParseData:
    def __init__(self, start, end, data):
        self.start = start
        self.end = end
        self.data = data


class MastNode:
    def add_child(self, cmd):
        #print("ADD CHILD")
        pass

    def compile_formatted_string(self, message):
        if "{" in message:
            message = f'''f"""{message}"""'''
            code = compile(message, "<string>", "eval")
            return code
        else:
            return message

    @classmethod
    def parse(cls, lines):
        mo = cls.rule.match(lines)

        if mo:
            span = mo.span()
            data = mo.groupdict()
            return ParseData(span[0], span[1], data)
        else:
            return None

        



class Label(MastNode):
    rule = re.compile(r'(?P<m>=|\?){2,}\s*(?P<name>\w+)\s*(?P=m){2,}')

    def __init__(self, name, m=None, loc=None):
        self.name = name
        self.cmds = []
        self.next = None
        self.loc = loc

    def add_child(self, cmd):
        self.cmds.append(cmd)



class Log(MastNode):
    rule = re.compile(r"""log\s+(name\s+(?P<logger>[\w\.]*)\s+)?(?P<q>['"]{3}|["'])(?P<message>[\s\S]+?)(?P=q)(\s+(?P<level>debug|info|warning|error|critical))?""")
    
    def __init__(self, message, logger=None, level=None, q=None, loc=None):
        self.message = self.compile_formatted_string(message)
        self.level = level if level is not None else "debug"
        self.logger = logger if logger is not None else "mast.story"
        self.loc = loc

class Logger(MastNode):
    rule = re.compile(r"""logger(\s+name\s+(?P<logger>[\w\.]*))?(\s+string\s+(?P<var>\w*))?(\s+file\s*(?P<q>['"]{3}|["'])(?P<name>[\s\S]+?)(?P=q))?""")

    def __init__(self, logger=None, var=None, name=None, q=None, loc=None):
        self.var = var
        if name is not None:
            name = self.compile_formatted_string(name)
        self.name = name
        self.logger = logger if logger is not None else "mast.story"
        self.loc = loc

class LoopStart(MastNode):
    rule = re.compile(r'(for\s*(?P<name>\w+)\s*)(in|while)((?P<if_exp>[\s\S]+?))'+BLOCK_START)
    loop_stack = []
    def __init__(self, if_exp=None, name=None, loc=None):
        if if_exp:
            if_exp = if_exp.lstrip()
            self.code = compile(if_exp, "<string>", "eval")
        else:
            self.code = None
        self.name = name
        self.iter = None
        self.loc = loc
        self.end = None
        LoopStart.loop_stack.append(self)


class LoopBreak(MastNode):
    rule = re.compile(r'(?P<op>break|continue)\s*(?P<name>\w+)')
    def __init__(self, op=None, name=None, loc=None):
        self.name = name
        self.op = op
        self.start = LoopStart.loop_stack[-1]
        self.loc = loc

class LoopEnd(MastNode):
    rule = re.compile(r'((?P<loop>next)\s*(?P<name>\w+))')
    def __init__(self, loop=None, name=None, loc=None):
        self.loop = True if loop is not None and 'next' in loop else False
        self.name = name
        self.start = LoopStart.loop_stack.pop()
        self.loc = loc
        self.start.end = self


class IfStatements(MastNode):
    rule = re.compile(r'((?P<end>else:|end_if)|(((?P<if_op>if|elif)\s+?(?P<if_exp>[\s\S]+?)'+BLOCK_START+')))')

    if_chains = []

    def __init__(self, end=None, if_op=None, if_exp=None, loc=None):

        if if_exp:
            if_exp = if_exp.lstrip()
            self.code = compile(if_exp, "<string>", "eval")
        else:
            self.code = None

        self.end = end
        self.if_op = if_op
        self.if_chain = None
        self.if_node = None
        self.loc = loc


        if "end_if" == self.end:
            self.if_node = IfStatements.if_chains[-1]
            IfStatements.if_chains[-1].if_chain.append(loc)
            IfStatements.if_chains.pop()
        elif "else:" == self.end:
            self.if_node = IfStatements.if_chains[-1]
            IfStatements.if_chains[-1].if_chain.append(loc)
        elif "elif" == self.if_op:
            self.if_node = IfStatements.if_chains[-1]
            IfStatements.if_chains[-1].if_chain.append(loc)
        elif "if" == self.if_op:
            self.if_chain = [loc]
            IfStatements.if_chains.append(self)

class MatchStatements(MastNode):
    rule = re.compile(r'((?P<end>case\s*_:|end_match)|(((?P<op>match|case)\s+?(?P<exp>[\s\S]+?)'+BLOCK_START+')))')
    chains = []
    def __init__(self, end=None, op=None, exp=None, loc=None):
        self.loc = loc
        self.match_exp = None
        self.end = end
        self.op = op
        self.chain = None
        self.match_node = None

        if "end_match" == end:
            the_match_node = MatchStatements.chains[-1]
            self.match_node = the_match_node
            the_match_node.chain.append(loc)
            MatchStatements.chains.pop()
        elif end is not None and end.startswith("case"):
            the_match_node = MatchStatements.chains[-1]
            self.match_node = the_match_node
            the_match_node.chain.append(loc)
            self.end = "case_:"
        elif "case" == op:
            the_match_node = MatchStatements.chains[-1]
            self.match_node = the_match_node
            the_match_node.chain.append(loc)
        elif "match" == op:
            self.match_node = self
            self.chain = []
            MatchStatements.chains.append(self)
        
        if op == "match":
            self.match_exp = exp.lstrip()
        elif exp:
            exp = exp.lstrip()
            exp = self.match_node.match_exp +"==" + exp
            self.code = compile(exp, "<string>", "eval")
        else:
            self.code = None


class PyCode(MastNode):
    rule = re.compile(r'((\~{2,})\n?(?P<py_cmds>[\s\S]+?)\n?(\~{2,}))')

    def __init__(self, py_cmds=None, loc=None):
        self.loc = loc
        if py_cmds:
            py_cmds= py_cmds.lstrip()
            self.code = compile(py_cmds, "<string>", "exec")

class DoCommand(MastNode):
    rule = re.compile(r'do\s+(?P<py_cmds>.+)')
    def __init__(self, py_cmds=None, loc=None):
        self.loc = loc
        if py_cmds:
            py_cmds= py_cmds.lstrip()
            self.code = compile(py_cmds, "<string>", "exec")




class Input(MastNode):
    rule = re.compile(r'input\s+(?P<name>\w+)')

    def __init__(self, name, loc=None):
        self.loc = loc
        self.name = name

class Import(MastNode):
    rule = re.compile(r'(from\s+(?P<lib>[\w\.\\\/-]+)\s+)?import\s+(?P<name>[\w\.\\\/-]+)')

    def __init__(self, name, lib=None, loc=None):
        self.loc = loc
        self.name = name
        self.lib = lib


class Comment(MastNode):
    #rule = re.compile(r'(#[ \t\S]*)|((?P<com>[!]{3,})[\s\S]+(?P=com))')
    rule = re.compile(r'(#[ \t\S]*)|(\/\*[\s\S]+\*\/)|([!]{3,}\s*(?P<com>\w+)\s*[!]{3,}[\s\S]+[!]{3,}\s*end\s+(?P=com)\s*[!]{3,})')

    def __init__(self, com=None, loc=None):
        self.loc = loc

class Marker(MastNode):
    rule = re.compile(r'[-*+]{3,}')
    def __init__(self, loc=None):
        self.loc = loc


class Scope(Enum):
    SHARED = 1  # per mast instance
    NORMAL = 2  # per scheduler
    TEMP = 99  # Per task?
    UNKNOWN = 100

class MastDataObject(object):
    def __init__(self, dictionary):
        # for dictionary in initial_data:
        for key in dictionary:
            setattr(self, key, dictionary[key])

    def __repr__(self):
        return repr(vars(self))

class Assign(MastNode):
    # '|'+STRING_REGEX+
    rule = re.compile(
        r'(?P<scope>(shared|temp)\s+)?(?P<lhs>[\w\.\[\]]+)\s*=\s*(?P<exp>('+PY_EXP_REGEX+'|'+STRING_REGEX+'|.*))')

    """ Not this doesn't support destructuring. To do so isn't worth the effort"""
    def __init__(self, scope, lhs, exp, quote=None, py=None, loc=None):
        self.lhs = lhs
        self.loc = loc
        self.scope = None if scope is None else Scope[scope.strip(
        ).upper()]
        
        #print(f"quote: {quote}")
        exp = exp.lstrip()
        if quote:
            exp = 'f'+exp        
        if py:
            exp = exp[2:-2]
            exp = exp.strip()
        self.code = compile(exp, "<string>", "eval")



class Jump(MastNode):
    rule = re.compile(r"""((?P<pop><<-((?P<pop_jump_type>>>|>)\s*(?P<pop_jump>\w+))?)|(->(?P<push>>)?\s*(?P<jump>\w+)))""")

    def __init__(self, pop, pop_jump_type, pop_jump, push, jump, loc=None):
        self.loc = loc
        self.label = jump
        self.push = push == ">"
        self.pop = pop is not None
        self.pop_jump = None
        self.pop_push = None
        if pop_jump_type is not None:
            if pop_jump_type == ">>":
                self.pop_push = pop_jump.strip()
            else:
                self.pop_jump = pop_jump.strip()



class Parallel(MastNode):
    """
    Creates a new 'task' to run in parallel
    """
    task_name =  re.compile(r"""await\s(?P<name>\w+)""")
    spawn_rule = re.compile("""((?P<name>\w+)\s*)?\=>(?P<all_any>\=>)?(\s*(?P<conditional>\w+)\s*\?)?\s*(?P<labels>\s*(\w+)((\s*[\|&]\s*)\w+)*)(?P<inputs>\s*"""+ DICT_REGEX+")?")
    #await_rule = re.compile(r"await\s+")
    await_return_rule = re.compile(r"await\s*(?P<ret>->)?\s*")
    block_rule = re.compile(r"\s*:")

    def __init__(self, name=None, is_block=None, await_task=None, reflect=None, all_any=None, conditional=None,  labels=None, inputs=None, loc=None):
        self.loc = loc
        self.name = name
        self.conditional = conditional
        self.labels = labels
        self.await_task = await_task
        self.code = None
        self.reflect = reflect
        self.end_await_node = None
        self.minutes = 0
        self.seconds = 0
        self.timeout_label = None
        self.fail_label = None
        if is_block:
            self.timeout_label = None
            self.fail_label = None
            EndAwait.stack.append(self)

        if await_task and name:
            self.await_task = True
            return

        
        if '|' in labels and '&' in labels:
             raise Exception("Mixing sequence (&) and fallback (|) is not allowed")
        self.sequence =  '&' in labels
        self.fallback =  '|' in labels
        self.labels = labels
        self.all_any = True if all_any is not None else False
        if self.sequence:
            self.labels = re.split(r'\s*&\s*', labels)
        elif self.fallback:
            self.labels = re.split(r'\s*\|\s*', labels)

        if inputs:
            inputs = inputs.lstrip()
            self.code = compile(inputs, "<string>", "eval")
        

    @classmethod
    def parse(cls, lines):

        match_task_await =  Parallel.task_name.match(lines) 
        if match_task_await:
            span = match_task_await.span()
            data = match_task_await.groupdict()
            data["await_task"] = True
            end = span[1]
            block =  Parallel.block_rule.match(lines[end:])
            
            if block:
                end+= block.span[1]
                data["is_block"] = True
            
            
            return ParseData(span[0], end, data)

        match_await =  Parallel.await_return_rule.match(lines)
        if match_await:
            await_span = match_await.span()
            await_len = await_span[1]-await_span[0]
            reflect_return = match_await.groupdict().get("ret", None)
            reflect_return = reflect_return  is not None
            lines = lines[await_span[1]:]
            spawn =  Parallel.spawn_rule.match(lines)
            if spawn is not None:
                span = spawn.span()
                data = spawn.groupdict()
                data["await_task"] = True
                data["reflect"] = reflect_return
                end = span[1]
                block =  Parallel.block_rule.match(lines[end:])
                
                if block:
                    span = block.span()
                    end = end + span[1]
                    line = lines[end:]
                    data["is_block"] = True
                return ParseData(await_span[0], await_len+end, data)
            else:
                return None

        mo =  Parallel.spawn_rule.match(lines)
        if mo:
            span = mo.span()
            data = mo.groupdict()
            return ParseData(span[0], span[1], data)
        else:
            return None

        
class EndAwait(MastNode):
    rule = re.compile(r'end_await')
    stack = []
    def __init__(self, loc=None):
        self.loc = loc
        EndAwait.stack[-1].end_await_node = self
        EndAwait.stack.pop()


class Event(MastNode):
    rule = re.compile(r'(event\s+(?P<event>[\w|_]+)'+BLOCK_START+')|(end_event)')
    stack = []
    def __init__(self, event=None, loc=None):
        self.loc = loc
        self.end = None
        self.event = event
        if event is None:
            Event.stack[-1].end = self
            Event.stack.pop()
        else:
            Event.stack.append(self)

MIN_SECONDS_REGEX = r"""(\s*((?P<minutes>\d+))m)?(\s*((?P<seconds>\d+)s))?"""
TIMEOUT_REGEX = r"(\s*timeout"+MIN_SECONDS_REGEX + r")?"
class Timeout(MastNode):
    rule = re.compile(r'timeout(\s*((?P<minutes>\d+))m)?(\s*((?P<seconds>\d+)s))?:')
    def __init__(self, minutes, seconds, loc=None):
        self.loc = loc
        
        self.await_node = EndAwait.stack[-1]
        EndAwait.stack[-1].timeout_label = self
        self.await_node.seconds = 0 if  seconds is None else int(seconds)
        self.await_node.minutes = 0 if  minutes is None else int(minutes)


class AwaitFail(MastNode):
    rule = re.compile(r'fail:')
    def __init__(self, loc=None):
        self.loc = loc
        
        self.await_node = EndAwait.stack[-1]
        EndAwait.stack[-1].fail_label = self



class AwaitCondition(MastNode):
    """
    waits for an existing or a new 'task' to run in parallel
    this needs to be a rule before Parallel
    """
    rule = re.compile(r"""await\s+until\s+(?P<if_exp>[^:]+)"""+BLOCK_START)
                      
    def __init__(self, minutes=None, seconds=None, if_exp=None, loc=None):
        self.loc = loc
        self.timeout_label = None
        self.end_await_node = None
        self.fail_label = None

        # Done int timeout now
        #self.seconds = 0 if  seconds is None else int(seconds)
        #self.minutes = 0 if  minutes is None else int(minutes)
        
        EndAwait.stack.append(self)

        if if_exp:
            if_exp = if_exp.lstrip()
            self.code = compile(if_exp, "<string>", "eval")
        else:
            self.code = None


class Cancel(MastNode):
    """
    Cancels a new 'task' to run in parallel
    """
    rule = re.compile(r"""cancel\s*(?P<name>[\w\.\[\]]+)""")

    def __init__(self, lhs=None, name=None, loc=None):
        self.loc = loc
        self.name = name


class End(MastNode):
    rule = re.compile(r'->\s*END\s*'+IF_EXP_REGEX)
    def __init__(self,  if_exp=None, loc=None):
        self.loc = loc
        if if_exp:
            if_exp = if_exp.lstrip()
            self.if_code = compile(if_exp, "<string>", "eval")
        else:
            self.if_code = None

class ReturnIf(MastNode):
    rule = re.compile(r'->\s*RETURN'+IF_EXP_REGEX)
    def __init__(self, if_exp=None,  loc=None):
        self.loc = loc
        if if_exp:
            if_exp = if_exp.lstrip()
            self.if_code = compile(if_exp, "<string>", "eval")
        else:
            self.if_code = None


class Fail(MastNode):
    rule = re.compile(r'->\s*FAIL'+IF_EXP_REGEX)
    def __init__(self, if_exp=None, loc=None):
        self.loc = loc
        if if_exp:
            if_exp = if_exp.lstrip()
            self.if_code = compile(if_exp, "<string>", "eval")
        else:
            self.if_code = None

class Delay(MastNode):
    clock = r"(\s*(?P<clock>\w+))"
    rule = re.compile(r'delay'+clock+MIN_SECONDS_REGEX)

    def __init__(self, clock, seconds=None, minutes=None, loc=None):
        self.loc = loc
        self.seconds = 0 if seconds is None else int(seconds)
        self.minutes = 0 if minutes is None else int(minutes)
        self.clock = clock


class Rule:
    def __init__(self, re, cls):
        self.re = re
        self.cls = cls



def first_non_space_index(s):
    for idx, c in enumerate(s):
        if not c.isspace():
            return idx
        if c == '\n':
            return idx
    return len(s)


def first_non_newline_index(s):
    for idx, c in enumerate(s):
        if c != '\n':
            return idx
    return len(s)


def first_newline_index(s):
    for idx, c in enumerate(s):
        if c == '\n':
            return idx
    return len(s)

class InlineData:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Mast:
    globals = {
        "math": math, 
        "faces": faces,
        "scatter": scatter,
        "random": random,
        "print": print, 
        "dir":dir, 
        "itertools": itertools,
        "next": next,
        "len": len,
        "reversed": reversed,
        "int": int,
        "min": min,
        "max": max,
        "abs": abs,
        "map": map,
        "filter": filter,
        "list": list,
        "set": set,
        "mission_dir": fs.get_mission_dir(),
        "data_dir": fs.get_artemis_data_dir(),
        "MastDataObject": MastDataObject,
        "range": range,
        "__build_class__":__build_class__, # ability to define classes
        "__name__":__name__ # needed to define classes?
    }
    inline_count = 0
    def __init__(self, cmds=None):
        self.lib_name = None

        if cmds is None:
            return
        if isinstance(cmds, str):
            cmds = self.compile(cmds)
        else:
            self.build(cmds)

    def make_global(func):
        add_to = Mast.globals
        add_to[func.__name__] = func


    def make_global_var(name, value):
        Mast.globals[name] = value
        

    def build(self, cmds):
        """
        Used to build via code not a script file
        should just process level things e.g. Input, Label, Var
        """
        self.clear()
        active = self.labels["main"]

        for cmd in cmds:
            match cmd.__class__.__name__:
                case "Input":
                    self.inputs[cmd.name] = cmd
                case "Label":
                    self.labels[cmd.name] = cmd
                    active.next = cmd
                    active = cmd
                case "Var":
                    self.vars[cmd.name] = cmd
                    active = cmd
                case _:
                    active.cmds.append(cmd)


    nodes = [
        Comment,
        Label,
        IfStatements,
        MatchStatements,
        LoopStart,
        LoopEnd,
        LoopBreak,
        PyCode,
        DoCommand,
        Log,
        Logger,
        Input,
        Event,
        #        Var,
        Import,
        AwaitCondition,
#        Await,  # needs to be before Parallel
        Timeout,
        EndAwait,
        AwaitFail,
        Parallel,  # needs to be before Assign
        Cancel,
        Assign,
        Fail,
        End,
        ReturnIf,
        Jump,
        
        Delay,
        Marker,
    ]

    def clear(self):
        self.inputs = {}
        self.vars = {"mast": self}
        self.labels = {}
        self.inline_labels = {}
        self.labels["main"] = Label("main")
        self.cmd_stack = [self.labels["main"]]
        self.indent_stack = [0]
        self.main_pruned = False
        self.schedulers = set()
        self.lib_name = None
        
    
    def prune_main(self):
        if self.main_pruned:
            return
        main = self.labels.get("main")
        # Convert all the assigned from the main into comments
        # removing is bad it will affect if statements
        if main is not None:
            for i in range(len(main.cmds)):
                cmd = main.cmds[i]
                if cmd.__class__ == Assign and cmd.scope == Scope.SHARED:
                    main.cmds[i] = Comment()
            self.main_pruned = True

    def add_scheduler(self, scheduler):
        self.schedulers.add(scheduler)

    def refresh_schedulers(self, source, label):
        for scheduler in self.schedulers:
            if scheduler == source:
                continue
            scheduler.refresh(label)

    def remove_scheduler(self, scheduler):
        self.schedulers.remove(scheduler)

    def from_file(self, file_name, lib_name=None):
        """ Docstring"""
        content = None
        errors= None
        if self.lib_name is not None:
            content, errors = self.content_from_lib_or_file(file_name, self.lib_name)
        else:
            content, errors = self.content_from_lib_or_file(file_name, lib_name)
            if lib_name is not None and content is not None:
                self.lib_name = lib_name
        if errors is not None:
            return errors
        if content is not None:
            errors = self.compile(content)
            if len(errors) > 0:
                message = f"Compile errors\nCannot compile file {file_name}"
                errors.append(message)
            return errors
        return []
        

    def process_file_content(self,content, file_name):
        file_name, ext = os.path.splitext(file_name)
        errors = []
        match ext:
            case _:
                if content is not None:
                    errors = self.compile(content)

                    if len(errors) > 0:
                        message = f"Compile errors\nCannot compile file {file_name}"
                        errors.append(message)

        return errors
        

    # def from_lib_file(self, file_name, lib_name):
    #     lib_name = os.path.join(fs.get_mission_dir(), lib_name)
    #     content = None

    #     errors = []
    #     try:
    #         with ZipFile(lib_name) as lib_file:
    #             with lib_file.open(file_name) as f:
    #                 content = f.read().decode('UTF-8')
    #                 self.lib_name = lib_name
    #                 return self.process_file_content(content, file_name)
    #     except:
    #         message = f"File load error\nCannot load file {file_name}"
    #         print(message)
    #         errors.append(message)
    #     return errors
        

    def content_from_lib_or_file(self, file_name, lib_name):
        try:
            if lib_name is not None:
                lib_name = os.path.join(fs.get_mission_dir(), lib_name)
                with ZipFile(lib_name) as lib_file:
                    with lib_file.open(file_name) as f:
                        content = f.read().decode('UTF-8')
                        return content, None
                    
            else:
                file_name = os.path.join(fs.get_mission_dir(), file_name)
                self.basedir = os.path.dirname(file_name)
                with open(file_name) as f:
                    content = f.read()
                return content, None
        except:
            message = f"File load error\nCannot load file {file_name}"
            return None, [message]
            
        
    

    def import_content(self, filename, lib_file):
        add = self.__class__()
        errors = add.from_file(filename, lib_file)
        if len(errors)==0:
            for label, node in add.labels.items():
                if label == "main":
                    main = self.labels["main"]
                    main.cmds.extend(node.cmds)
                else:
                    self.labels[label] = node
        return errors

    def compile(self, lines):
        self.clear()
        line_no = 0
        errors = []
        active = self.labels.get("main")
        while len(lines):
            mo = first_non_newline_index(lines)
            line_no += mo if mo is not None else 0
            #line = lines[:mo]
            lines = lines[mo:]
            parsed = False
            indent = first_non_space_index(lines)
            if indent is None:
                continue
            ###########################################
            ### Support indent as meaningful
            ###########################################
            # if indent > self.indent_stack[-1]:
            #     # new indent
            #     self.cmd_stack.append(active_cmd)
            #     self.indent_stack.append(indent)
            # while indent < self.indent_stack[-1]:
            #     self.cmd_stack.pop()
            #     self.indent_stack.pop()
            if indent > 0:
                # strip spaces
                lines = lines[indent:]
            if len(lines)==0:
                break

            for node_cls in self.__class__.nodes:
                #mo = node_cls.rule.match(lines)
                mo = node_cls.parse(lines)
                if mo:
                    #span = mo.span()
                    data = mo.data

                    line = lines[mo.start:mo.end]
                    lines = lines[mo.end:]
                    line_no += line.count('\n')
                    parsed = True
                
                    
                    logger = logging.getLogger("mast.compile")
                    logger.debug(f"PARSED: {node_cls.__name__:} {line}")

                    match node_cls.__name__:
                        case "Label":
                            next = Label(**data)
                            active.next = next
                            active = next
                            self.labels[data['name']] = active
                            self.cmd_stack.pop()
                            self.cmd_stack.append(active)
                        case "Input":
                            input = Input(**data)
                            self.inputs[data['name']] = input

                        case "Import":
                            lib_name = data.get("lib")
                            err = self.import_content(data['name'], lib_name)
                            if err is not None:
                                errors.extend(err)
                                for e in err:
                                    print("import error "+e)


                        # Throw comments and markers away
                        case "Comment":
                            pass
                        case "Marker":
                            pass

                        case _:
                            try:
                                loc = len(self.cmd_stack[-1].cmds)
                                obj = node_cls(loc=loc, **data)
                            except Exception as e:
                                logger = logging.getLogger("mast.compile")
                                logger.error(f"ERROR: {line_no} - {line}")
                                logger.error(f"Exception: {e}")

                                errors.append(f"ERROR: {line_no} - {line}")
                                errors.append(f"Exception: {e}")
                                return errors # return with first errors

                            obj.line_no = line_no
                            self.cmd_stack[-1].add_child(obj)
                    break
            if not parsed:
                mo = first_non_newline_index(lines)

                if mo:
                    # this just blank lines
                    line_no += mo
                    line = lines[:mo]
                    lines = lines[mo:]
                else:
                    mo = first_newline_index(lines)

                    logger = logging.getLogger("mast.compile")
                    logger.error(f"ERROR: {line_no} - {lines[0:mo]}")

                    errors.append(f"ERROR: {line_no} - {lines[0:mo]}")
                    lines = lines[mo+1:]
        return errors

    def enable_logging():
        logger = logging.getLogger("mast")
        handler  = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s|%(name)s|%(message)s"))
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        # fh = logging.FileHandler('mast.log')
        # fh.setLevel(logging.DEBUG)
        # logger.addHandler(fh)
        




