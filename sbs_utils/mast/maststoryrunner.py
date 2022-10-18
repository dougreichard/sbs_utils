import logging
from .mastrunner import PollResults, MastRuntimeNode, MastRunner, MastAsync, Scope
from .mast import Mast
import sbs
from ..gui import FakeEvent, Gui, Page

from ..pages import layout
from ..tickdispatcher import TickDispatcher

from .errorpage import ErrorPage
from .maststory import AppendText, ButtonControl, MastStory, Choose, Text, Blank, Ship, Face, Row, Section, Area, Refresh, SliderControl, CheckboxControl
import traceback
from .mastsbsrunner import MastSbsRunner, Button

class StoryRuntimeNode(MastRuntimeNode):
    def on_message(self, sim, event):
        pass
    def databind(self):
        return False

class FaceRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Face):
        tag = thread.main.page.get_tag()
        face = node.face
        if node.code:
            face = thread.eval_code(node.code)
        if face is not None:
            self.layout_item = layout.Face(face, tag)
            thread.main.page.add_content(self.layout_item, self)

    def poll(self, mast, thread, node:Face):
        return PollResults.OK_ADVANCE_TRUE

class RefreshRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Refresh):
        thread.main.mast.refresh_runners(thread.main, node.label)
        

class ShipRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Ship):
        tag = thread.main.page.get_tag()
        thread.main.page.add_content(layout.Ship(node.ship, tag), self)


class TextRunner(StoryRuntimeNode):
    current = None
    def enter(self, mast:Mast, thread:MastAsync, node: Text):
        self.tag = thread.main.page.get_tag()
        msg = ""
        # for databind
        self.node = node
        self.thread = thread 
        value = True
        if node.code is not None:
            value = thread.eval_code(node.code)
        if value:
            msg = thread.format_string(node.message)
            self.layout_text = layout.Text(msg, self.tag)
            TextRunner.current = self
            thread.main.page.add_content(self.layout_text, self)

    def databind(self):
        value = True
        if self.node.code is not None:
            value = self.thread.eval_code(self.node.code)
        if value:
            msg = self.thread.format_string(self.node.message)
            if self.layout_text.message !=msg:
                self.layout_text.message = msg
                return True
        return False
        

class AppendTextRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: AppendText):
        msg = ""
        value = True
        if node.code is not None:
            value = thread.eval_code(node.code)
        if value:
            msg = thread.format_string(node.message)
            text = TextRunner.current
            if text is not None:
                text.layout_text.message += '\n'
                text.layout_text.message += msg

class ButtonControlRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: ButtonControl):
        self.data = None
        if node.is_end == False:
            
            self.tag = thread.main.page.get_tag()
            value = True
            
            if node.code is not None:
                value = self.thread.eval_code(node.code)
            if value:
                msg = thread.format_string(node.message)
                thread.main.page.add_content(layout.Button(msg, self.tag), self)
            if node.data_code is not None:
                self.data = thread.eval_code(node.data_code)
                
        self.node = node
        self.thread = thread

        
    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            # Jump to the cmds after the button
            self.thread.push_label(self.thread.active_label, self.node.loc+1, self.data)

    def poll(self, mast:Mast, thread:MastAsync, node: ButtonControl):
        if node.is_end:
            self.thread.pop_label()
            return PollResults.OK_JUMP
        elif node.end_node:
            self.thread.jump(self.thread.active_label, node.end_node.loc+1)
            return PollResults.OK_JUMP
        



class RowRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Row):
        thread.main.page.add_row()
        

class BlankRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Blank):
        tag = thread.main.page.get_tag()
        thread.main.page.add_content(layout.Separate(), self)

class SectionRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Section):
        thread.main.page.add_section()

class AreaRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Area):
        thread.main.page.set_section_size(node.left, node.top, node.right, node.bottom)


class ChooseRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: Choose):
        seconds = (node.minutes*60+node.seconds)
        if seconds == 0:
            self.timeout = None
        else:
            self.timeout = TickDispatcher.current + (node.minutes*60+node.seconds)*TickDispatcher.tps

        
        button_layout = layout.Layout(None, 30,95,90,100)

        active = 0
        index = 0
        row: Row
        layout_row = layout.Row()
        for button in node.buttons:
            match button.__class__.__name__:
                case "Button":
                    value = True
                    #button.end_await_node = node.end_await_node
                    if button.code is not None:
                        value = thread.eval_code(button.code)
                    if value and button.should_present(0):#thread.main.client_id):
                        runner = ChoiceButtonRunner(self, index, thread.main.page.get_tag(), button)
                        #runner.enter(mast, thread, button)
                        msg = thread.format_string(button.message)
                        layout_button = layout.Button(msg, runner.tag)
                        layout_row.add(layout_button)
                        thread.main.page.add_tag(runner)
                        active += 1
                case "Separator":
                    # Handle face expression
                    layout_row.add(layout.Separate())
            index+=1

        if active>0:    
            button_layout.add(layout_row)
            thread.main.page.set_button_layout(button_layout)
        else:
            thread.main.page.set_button_layout(None)

        self.active = active
        self.buttons = node.buttons
        self.button = None


    def poll(self, mast:Mast, thread:MastAsync, node: Choose):
        if self.active==0 and self.timeout is None:
            return PollResults.OK_ADVANCE_TRUE


        if self.button is not None:
            if node.assign:
                thread.set_value_keep_scope(node.assign, self.button.index)
                return PollResults.OK_ADVANCE_TRUE

            self.button.node.visit(self.button.client_id)
            button = self.buttons[self.button.index]
            self.button = None
            thread.jump(thread.active_label,button.loc+1)
            return PollResults.OK_JUMP

        if self.timeout:
            if self.timeout <= TickDispatcher.current:
                if node.timeout_label:
                    thread.jump(thread.active_label,node.timeout_label.loc+1)
                    return PollResults.OK_JUMP
                elif node.end_await_node:
                    thread.jump(thread.active_label,node.end_await_node.loc+1)
                    return PollResults.OK_JUMP
        return PollResults.OK_RUN_AGAIN


class ChoiceButtonRunner(StoryRuntimeNode):
    def __init__(self, choice, index, tag, node):
        self.choice = choice
        self.index = index
        self.tag = tag
        self.client_id = None
        self.node = node
        
    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.choice.button = self
            self.client_id = event.client_id
    



class SliderControlRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: SliderControl):
        self.tag = thread.main.page.get_tag()
        self.node = node
        scoped_val = thread.get_value(self.node.var, self.node.value)
        val = scoped_val[0]
        self.scope = scoped_val[1]
        self.layout = layout.Slider(val, node.low, node.high, self.tag)
        self.thread = thread

        thread.main.page.add_content(self.layout, self)

    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            if self.node.is_int:
                self.layout.value = int(event.sub_float)
            else:
                self.layout.value = event.sub_float
            self.thread.set_value(self.node.var, self.layout.value, self.scope)


class CheckboxControlRunner(StoryRuntimeNode):
    def enter(self, mast:Mast, thread:MastAsync, node: SliderControl):
        self.tag = thread.main.page.get_tag()
        self.node = node
        scoped_val = thread.get_value(self.node.var, False)
        val = scoped_val[0]
        self.scope = scoped_val[1]
        msg = thread.format_string(node.message)
        self.layout = layout.Checkbox(msg, self.tag, val)
        self.thread = thread
        thread.main.page.add_content(self.layout, self)

    def on_message(self, sim, event):
        if event.sub_tag == self.tag:
            self.layout.value = not self.layout.value
            self.thread.set_value(self.node.var, self.layout.value, self.scope)
            self.layout.present(sim, event)
            


over =     {
    "Row": RowRunner,
    "Text": TextRunner,
    "AppendText": AppendTextRunner,
    "Face": FaceRunner,
    "Ship": ShipRunner,
    "ButtonControl": ButtonControlRunner,
    "SliderControl": SliderControlRunner,
    "CheckboxControl": CheckboxControlRunner,
    "Blank": BlankRunner,
    "Choose": ChooseRunner,
    "Section": SectionRunner,
    "Area": AreaRunner,
    "Refresh": RefreshRunner

}

class StoryRunner(MastSbsRunner):
    def __init__(self, mast: Mast, overrides=None):
        if overrides:
            super().__init__(mast, over|overrides)
        else:
            super().__init__(mast,  over)
        self.sim = None
        self.paint_refresh = False
        self.errors = []

    def run(self, sim, client_id, page, label="main", inputs=None):
        self.sim = sim
        self.page = page
        inputs = inputs if inputs else {}
        self.vars['sim'] = sim
        self.vars['client_id'] = client_id
        self.vars['IS_SERVER'] = client_id==0
        self.vars['IS_CLIENT'] = client_id!=0
        super().start_thread( label, inputs)

    def story_tick_threads(self, sim, client_id):
        self.sim = sim
        self.client_id = client_id
        return super().sbs_tick_threads(sim)

    def refresh(self, label):
        for thread in self.threads:
            if label == thread.active_label:
                thread.jump(thread.active_label)
                self.story_tick_threads(self.sim, self.client_id)
                Gui.dirty(self.client_id)

    def runtime_error(self, message):
        if self.sim:
            sbs.pause_sim()
        err = traceback.format_exc()
        if not err.startswith("NoneType"):
            message += str(err)
            self.errors = [message]
            
        

class StoryPage(Page):
    tag = 0
    story_file = None
    inputs = None
    story = None
    def __init__(self) -> None:
        self.gui_state = 'repaint'
        self.story_runner = None
        self.layouts = []
        self.pending_layouts = self.pending_layouts = [layout.Layout(None, 20,10, 100, 90)]
        self.pending_row = self.pending_row = layout.Row()
        self.pending_tag_map = {}
        self.tag_map = {}
        self.aspect_ratio = sbs.vec2(1920,1071)
        self.client_id = None
        self.sim = None
        #self.tag = 0
        self.errors = []
        cls = self.__class__
        
        if cls.story is None:
            if cls.story is  None:
                cls.story = MastStory()
                self.errors =  cls.story.from_file(cls.story_file)
        

    def start_story(self, sim, client_id):
        if self.story_runner is not None:
            return
        cls = self.__class__
        if len(self.errors)==0:
            self.story_runner = StoryRunner(cls.story)
            if cls.inputs:
                self.story_runner.run(sim, client_id, self, inputs=cls.inputs)
            else:
                self.story_runner.run(sim, client_id, self)
            TickDispatcher.do_interval(sim, self.tick_mast, 0)

    def tick_mast(self, sim, t):
        if self.story_runner:
            self.story_runner.story_tick_threads(sim, self.client_id)

   

    def swap_layout(self):
        self.layouts = self.pending_layouts
        self.tag_map = self.pending_tag_map
        self.tag = 0
        
        if self.layouts:
            for layout_obj in self.layouts:
                layout_obj.calc()
            
            self.pending_layouts = self.pending_layouts = [layout.Layout(None, 20,10, 100, 90)]
            self.pending_row = self.pending_row = layout.Row()
            self.pending_tag_map = {}
        
        self.gui_state = 'repaint'

    def get_tag(self):
        self.tag += 1
        return str(self.tag)

    def add_row(self):
        if not self.pending_layouts:
            self.pending_layouts = [layout.Layout(None, 20,10, 100, 90)]
        if self.pending_row:
            if len(self.pending_row.columns):
                self.pending_layouts[-1].add(self.pending_row)
        if self.pending_tag_map is None:
            self.pending_tag_map = {}
        self.pending_row = layout.Row()

    def add_tag(self, layout_item):
        if self.pending_tag_map is None:
            self.pending_tag_map = {}

        if hasattr(layout_item, 'tag'):
            self.pending_tag_map[layout_item.tag] = layout_item

    def add_content(self, layout_item, runner):
        if self.pending_layouts is None:
            self.add_row()

        self.add_tag(runner)
        self.pending_row.add(layout_item)

    
    def add_section(self):
        if not self.pending_layouts:
            self.pending_layouts = [layout.Layout(None, 20,10, 100, 90)]
        else:
            self.add_row()
            self.pending_layouts.append(layout.Layout(None, 20,10, 100, 90))

    def set_section_size(self, left, top, right, bottom):
        #print( f"SIZE: {left} {top} {right} {bottom}")
        if not self.pending_layouts:
            self.add_row()
        l = self.pending_layouts[-1]
        l.set_size(left,top, right, bottom)
    

    def set_button_layout(self, layout):
        if self.pending_row and self.pending_layouts:
            if self.pending_row:
                self.pending_layouts[-1].add(self.pending_row)
        
        if not self.pending_layouts:
            self.add_section()

        if layout:
            self.pending_layouts.append(layout)
        
        self.swap_layout()
    
    def present(self, sim, event):
        """ Present the gui """
        if self.gui_state == "errors":
            return
        if self.story_runner is None:
            self.start_story(sim, event.client_id)
        else:
            if len(self.story_runner.errors) > 0:
                #errors = self.errors.reverse()
                message = "Compile errors\n".join(self.story_runner.errors)
                sbs.send_gui_clear(event.client_id)
                sbs.send_gui_text(event.client_id, message, "error", 30,20,100,100)
                self.gui_state = "errors"
                return

            if self.story_runner.paint_refresh:
                if self.gui_state != "repaint":  
                    self.gui_state = "refresh"
                self.story_runner.paint_refresh = False
            if not self.story_runner.story_tick_threads(sim, event.client_id):
                #self.story_runner.mast.remove_runner(self)
                Gui.pop(sim, event.client_id)
                return
        if len(self.errors) > 0:
            message = "Compile errors\n".join(self.errors)
            sbs.send_gui_clear(event.client_id)
            sbs.send_gui_text(event.client_id, message, "error", 30,20,100,100)
            self.gui_state = "errors"
            return
        
        sz = sbs.get_screen_size()
        if sz is not None and sz.y != 0:
            aspect_ratio = sz
            if (self.aspect_ratio.x != aspect_ratio.x or 
                self.aspect_ratio.y != aspect_ratio.y):
                self.aspect_ratio = sz
                for layout in self.layouts:
                    layout.aspect_ratio = aspect_ratio
                    layout.calc()
                self.gui_state = 'repaint'

        
        match self.gui_state:
            case  "repaint":
                sbs.send_gui_clear(event.client_id)
                # Setting this to a state we don't process
                # keeps the existing GUI displayed

                for layout in self.layouts:
                    layout.present(sim,event)
                
                self.gui_state = "presenting"
            case  "refresh":
                for layout in self.layouts:
                    layout.present(sim,event)
                self.gui_state = "presenting"


    def on_message(self, sim, event):
        
        message_tag = event.sub_tag
        runner = self.tag_map.get(message_tag)
        if runner:
            
            runner.on_message(sim, event)
            refresh = False
            for node in self.tag_map.values():
                if node != runner:
                    bound = node.databind()
                    refresh = bound or refresh
            if refresh:
                self.gui_state = "refresh"
            self.present(sim, event)

