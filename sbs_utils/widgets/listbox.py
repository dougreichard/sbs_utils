from ..gui import Widget
from .. import layout as layout
import sbs
from .. import faces


class Listbox(Widget):
    """
      A widget to list things passing function/lamdas to get the data needed for option display of
      - face
      - ship
      - icon
      - text
    """

    def __init__(self, left, top, tag_prefix, items, text=None, face=None, ship=None, select=False, multi=False, item_height=5) -> None:
        """ Listbox

        A widget Shows a list of things
     
        :param left: left coordinate
        :type left: float
        :param top: top coordinate
        :type top: float
        :param tag_prefix: Prefix to use in message tags to mak this component unique
        :type tag_prefix: str
        """
        super().__init__(left,top,tag_prefix)
        self.gui_state = "blank"
        self.cur = 0
        self.bottom = top+40
        self.right = left+33
        self.items = items
        self.text = text
        self.face = face
        self.ship = ship
        self.select = select
        self.multi= multi
        self.cur = 0 
        self.item_height = item_height # in percent
        self.square_width_percent = 0
        self.slots =[]
        self.selected = set()

    def present(self, sim, event):
        """ present

        builds/manages the content of the widget
     
        :param sim: simulation
        :type sim: Artemis Cosmos simulation
        :param CID: Client ID
        :type CID: int
        """
        CID = event.client_id
        screen_size = sbs.get_screen_size()
        aspect_ratio = screen_size.y /  screen_size.x
        # square_ratio = aspect_ratio_y
        # if screen_size.x < screen_size.y:
        #square_ratio = aspect_ratio
        # One percent in pixels
        square_width_percent = aspect_ratio * self.item_height
        square_height_percent = self.item_height
        
        # force redraw of on size change
        if square_width_percent != self.square_width_percent:
            self.gui_state = "redraw"
            self.square_width_percent = square_width_percent

        if self.gui_state == "presenting":
            return
        
        if self.items is None:
            sbs.send_gui_text(
                    CID, f"Error {self.test}", f"{self.tag_prefix}error", self.left, self.top, self.right, self.top+5)
            return

        left = self.left
        top = self.top
        cur = self.cur
        max_slot = (self.bottom-self.top)/self.item_height
        slot_count = len(self.items)-max_slot

        sbs.send_gui_slider(CID, f"{self.tag_prefix}cur", -slot_count,  0, -self.cur,
                    self.right-3, self.top,
                    self.right, self.bottom)
        slot= 0
        self.slots =[]
        
        
        while top+5 <= self.bottom:
            item = self.items[cur]
            # track what item is in what slot
            self.slots.append(cur)
            if self.ship: 
                ship_to_diplay = self.ship(item)
                sbs.send_gui_3dship(CID, ship_to_diplay, f"{self.tag_prefix}ship:{slot}", 
                    left, top,
                    left+square_width_percent, top+square_height_percent )
                left += square_width_percent
            if self.face: 
                face = self.face(item)
                sbs.send_gui_face(CID, face, f"{self.tag_prefix}face:{slot}", 
                    left, top,
                    left+square_width_percent, top+square_height_percent )
                left += square_width_percent
            text = ""
            if self.text:
                text = self.text(item)
            if self.select or self.multi:
                #print(f"{cur} selected {1 if cur in self.selected else 0}")
                sbs.send_gui_checkbox(
                    CID, text, f"{self.tag_prefix}name:{slot}", 1 if cur in self.selected else 0,
                        left, top, self.right-3.5, top+self.item_height)
            else:
                sbs.send_gui_text(
                    CID, text, f"{self.tag_prefix}name:{slot}", 
                        left, top, self.right, top+self.item_height)
            top += self.item_height
            cur += 1
            slot+=1
            if cur >= len(self.items):
                break
            left = self.left
        
        self.gui_state = "presenting"


    def on_message(self, sim, event):
        """ on_message

        handles messages this will look for components owned by this control and react accordingly
        components owned will have the tag_prefix
     
        :param sim: simulation
        :type sim: Artemis Cosmos simulation
        :param message_tag: Tag of the component
        :type message_tag: str
        :param CID: Client ID
        :type CID: int
        :param data: unused no component use data
        :type data: any
        """
        message_tag = event.sub_tag
        client_id = event.client_id

        if not message_tag.startswith(self.tag_prefix):
            return False

        message_tag = message_tag[len(self.tag_prefix):] 
        if message_tag == "cur":
                value = int(-event.sub_float)
                if value != self.cur:
                    self.cur = value
                    self.gui_state = "redraw"
                    self.present(sim, event)
                return True
        if message_tag.startswith('name:'):
            slot = int(message_tag[5:])
            item = int(self.slots[slot])
            # handle multi-select
            if self.multi:
                if item in self.selected:
                    self.selected.discard(item)
                else:
                    self.selected.add(item)
            else:
                self.selected = set()
                self.selected.add(item)
            self.gui_state = "redraw"
            self.present(sim, event)

                
        return False
    def get_selected(self):
        ret = []
        for item in self.selected:
            ret.append(self.items[item])
        return ret