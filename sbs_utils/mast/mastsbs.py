from .mast import IF_EXP_REGEX, TIMEOUT_REGEX, OPT_COLOR, Mast, MastNode, EndAwait,BLOCK_START
import re


class Target(MastNode):
    """
    Creates a new 'task' to run in parallel
    """
    rule = re.compile(r"""have\s*(?P<from_tag>[\w\.\[\]]+)\s*(?P<cmd>target|approach)(\s*(?P<to_tag>[\w\.\[\]]+))?""")
    def __init__(self, cmd=None, from_tag=None, to_tag=None, loc=None):
        self.loc = loc
        self.from_tag = from_tag
        self.to_tag = to_tag
        self.approach = cmd=="approach"

        
class Tell(MastNode):
    #rule = re.compile(r'tell\s+(?P<to_tag>\w+)\s+(?P<from_tag>\w+)\s+((['"]{3}|["'])(?P<message>[\s\S]+?)(['"]{3}|["']))')
    rule = re.compile(r"""have\s*(?P<from_tag>\*?\w+)\s+tell\s+(?P<to_tag>\*?\w+)\s+((['"]{3}|["'])(?P<message>[\s\S]+?)\4)"""+OPT_COLOR)
    def __init__(self, to_tag, from_tag, message, color=None, loc=None):
        self.loc = loc
        self.to_tag = to_tag
        self.from_tag = from_tag
        self.message = self.compile_formatted_string(message)
        self.color = color if color is not None else "#fff"

class Broadcast(MastNode):
    #rule = re.compile(r'tell\s+(?P<to_tag>\w+)\s+(?P<from_tag>\w+)\s+((['"]{3}|["'])(?P<message>[\s\S]+?)(['"]{3}|["']))')
    rule = re.compile(r"""have\s*(?P<to_tag>\*?\w+)\s+broadcast\s+(?P<q>['"]{3}|["'])(?P<message>[\s\S]+?)(?P=q)"""+OPT_COLOR)
    def __init__(self, to_tag, message, color=None, q=None,loc=None):
        self.to_tag = to_tag
        self.loc = loc
        self.message = self.compile_formatted_string(message)
        self.color = color if color is not None else "#fff"


class Comms(MastNode):
    rule = re.compile(r"""await\s*(?P<from_tag>\w+)\s*comms\s*(?P<to_tag>\w+)(\s*set\s*(?P<assign>\w+))?(\s+color\s*["'](?P<color>[ \t\S]+)["'])?"""+TIMEOUT_REGEX+'\s*'+BLOCK_START)
    def __init__(self, to_tag, from_tag, assign=None, minutes=None, seconds=None, time_pop=None,time_push="", time_jump="", color="white", loc=None):
        self.loc = loc
        self.to_tag = to_tag
        self.from_tag = from_tag
        self.assign = assign
        self.buttons = []
        self.seconds = 0 if  seconds is None else int(seconds)
        self.minutes = 0 if  minutes is None else int(minutes)
        self.color = color

        self.timeout_label = None
        self.fail_label = None
        self.end_await_node = None
        EndAwait.stack.append(self)

class Scan(MastNode):
    rule = re.compile(r"""await\s*(?P<from_tag>\w+)\s*scan\s*(?P<to_tag>\w+)"""+BLOCK_START)
    def __init__(self, to_tag, from_tag, loc=None):
        self.loc = loc
        self.to_tag = to_tag
        self.from_tag = from_tag
        self.buttons = []

        self.end_await_node = None
        EndAwait.stack.append(self)

class ScanResult(MastNode):
    rule = re.compile(r"""scan\s*results\s*((['"]{3}|["'])(?P<message>[\s\S]+?)\2)""")
    def __init__(self, message=None, loc=None):
        self.loc = loc
        self.message = message

FOR_RULE = r'(\s+for\s+(?P<for_name>\w+)\s+in\s+(?P<for_exp>[\s\S]+?))?'
class ScanTab(MastNode):
    rule = re.compile(r"""scan\s*tab\s+(?P<q>["'])(?P<message>.+?)(?P=q)"""+FOR_RULE+IF_EXP_REGEX+r"\s*"+BLOCK_START)
    def __init__(self, message=None, button=None,  
                 if_exp=None, 
                 for_name=None, for_exp=None, 
                 clone=False, q=None, loc=None):
        if clone:
            return
        self.message = self.compile_formatted_string(message)
        self.loc = loc
        self.await_node = EndAwait.stack[-1]
        self.await_node.buttons.append(self)

        if if_exp:
            if_exp = if_exp.lstrip()
            self.code = compile(if_exp, "<string>", "eval")
        else:
            self.code = None

        self.for_name = for_name
        self.data = None
        if for_exp:
            for_exp = for_exp.lstrip()
            self.for_code = compile(for_exp, "<string>", "eval")
        else:
            self.cor_code = None


    def clone(self):
        proxy = ScanTab(clone=True)
        proxy.message = self.message
        proxy.code = self.code
        proxy.loc = self.loc
        proxy.await_node = self.await_node
        proxy.data = self.data
        proxy.for_code = self.for_code
        proxy.for_name = self.for_name

        return proxy
    
    def expand(self):
        pass



FOR_RULE = r'(\s+for\s+(?P<for_name>\w+)\s+in\s+(?P<for_exp>[\s\S]+?))?'
class Button(MastNode):
    
    rule = re.compile(r"""(?P<button>\*|\+)\s+(?P<q>["'])(?P<message>.+?)(?P=q)"""+OPT_COLOR+FOR_RULE+IF_EXP_REGEX+r"\s*"+BLOCK_START)
    def __init__(self, message=None, button=None,  
                 color=None, if_exp=None, 
                 for_name=None, for_exp=None, 
                 clone=False, q=None, loc=None):
        if clone:
            return
        self.message = self.compile_formatted_string(message)
        self.sticky = (button == '+' or button=="button")
        self.color = color
        self.visited = set() if not self.sticky else None
        self.loc = loc
        self.await_node = EndAwait.stack[-1]
        self.await_node.buttons.append(self)

        if if_exp:
            if_exp = if_exp.lstrip()
            self.code = compile(if_exp, "<string>", "eval")
        else:
            self.code = None

        self.for_name = for_name
        self.data = None
        if for_exp:
            for_exp = for_exp.lstrip()
            self.for_code = compile(for_exp, "<string>", "eval")
        else:
            self.cor_code = None

    def visit(self, id_tuple):
        if self.visited is not None:
            self.visited.add(id_tuple)
    
    def been_here(self, id_tuple):
        if self.visited is not None:
            return (id_tuple in self.visited)
        return False

    def should_present(self, id_tuple):
        if self.visited is not None:
            return not id_tuple in self.visited
        return True

    def clone(self):
        proxy = Button(clone=True)
        proxy.message = self.message
        proxy.code = self.code
        proxy.color = self.color
        proxy.loc = self.loc
        proxy.await_node = self.await_node
        proxy.sticky = self.sticky
        proxy.visited = self.visited
        proxy.data = self.data
        proxy.for_code = self.for_code
        proxy.for_name = self.for_name

        return proxy
    
    def expand(self):
        pass



class ButtonSet(MastNode):
    rule = re.compile(r"""(button_set\s+use\s+(?P<use>\w+))|(button_set\s+clear\s+(?P<clear>\w+))|(button_set\s+((?P<append>append)\s+)?(?P<name>\w+)"""+BLOCK_START+r""")|(end_button_set)""")
    def __init__(self, use=None, name=None, clear=None, append=None, loc=None):
        self.loc = loc
        self.buttons = []
        self.use = use
        self.append = append is not None
        self.end = None
        self.name = name
        self.clear = False
        if clear:
            self.name = clear
            self.clear = True
            return
        elif use is not None:
            EndAwait.stack[-1].buttons.append(self)
        elif name is None:
            EndAwait.stack[-1].end = self
            self.end = self
            EndAwait.stack.pop(-1)
        else:
            EndAwait.stack.append(self)
    



class Near(MastNode):
    rule = re.compile(r'await\s*(?P<from_tag>\w+)\s+near\s+(?P<to_tag>\w+)\s*(?P<distance>\d+)'+TIMEOUT_REGEX+"\s*"+BLOCK_START)
    def __init__(self, to_tag, from_tag, distance, minutes=None, seconds=None, loc=None):
        self.loc = loc
        self.to_tag = to_tag
        self.from_tag = from_tag
        self.distance = 0 if distance is None else int(distance)
        
        self.seconds = 0 if  seconds is None else int(seconds)
        self.minutes = 0 if  minutes is None else int(minutes)

        self.timeout_label = None
        self.fail_label = None
        self.end_await_node = None
        EndAwait.stack.append(self)
    

class Simulation(MastNode):
    """
    Handle commands to the simulation
    """
    rule = re.compile(r"""simulation\s+(?P<cmd>pause|create|resume)""")
    def __init__(self, cmd=None, loc=None):
        self.loc = loc
        self.cmd = cmd

class Role(MastNode):
    """
    Handle commands to the simulation
    """
    rule = re.compile(r"""have\s+(?P<name>\w+)\s+(?P<cmd>add|remove)\s+(role|roles)\s*(?P<q>["'])(?P<roles>.+?)(?P=q)""")
    def __init__(self, name, roles, cmd=None, q=None, loc=None):
        self.loc = loc
        self.cmd = cmd
        self.name = name
        self.roles = [x.strip() for x in roles.split(',')]

class Find(MastNode):
    """
    
    """
    """ships = find all "Station" near artemis by 700  filter(lambda score: score >= 70)"""
    rule = re.compile(r"""(?P<assign>\w+)\s*=\s*all\s*(?P<q>["'])(?P<role>.+?)(?P=q)(\s*near\s+(?P<name>\w+)(\s+by\s+(?P<max>\d+))?)?(\s+filter\s*\((?P<the_filter>.*\)))?(\s*include\s+(?P<inc_dist>distance))?""")
    def __init__(self, assign, name, role,max, the_filter, inc_dist, q=None, loc=None):
        self.loc = loc
        self.all = all is not None
        self.name = name
        self.assign = assign
        self.role = role.strip()
        self.max = None if max is None else int(max)
        self.the_filter = the_filter
        self.inc_dist = inc_dist

class Closest(MastNode):
    """
    
    """
    """ships = find all "Station" near artemis by 700  filter(lambda score: score >= 70)"""
    rule = re.compile(r"""(?P<assign>\w+)\s*=\s*closest\s*(?P<q>["'])(?P<role>.+?)(?P=q)(\s*near\s+(?P<name>\w+)(\s+by\s+(?P<max>\d+))?)?(\s+filter\s*\((?P<the_filter>.*\)))?""")
    def __init__(self, assign, name, role,max, the_filter, q=None, loc=None):
        self.loc = loc
        self.all = all is not None
        self.name = name
        self.assign = assign
        self.role = role.strip()
        self.max = None if max is None else int(max)
        self.the_filter = the_filter



class MastSbs(Mast):
    nodes =  [
        # sbs specific
        Target,
        Tell,
        Broadcast,
        Comms,
        ButtonSet,
        Button,
        Near,
        Simulation,
        Role,
        Find,
        Closest,
        Scan,
        ScanTab,
        ScanResult
    ] + Mast.nodes 
    