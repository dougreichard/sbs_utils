from ..gui import Widget, get_client_aspect_ratio
from ..pages import layout as layout
import sbs
import struct # for images sizes
import os
from .. import fs
from ..helpers import FrameContext



class Listbox(Widget):
    """
      A widget to list things passing function/lamdas to get the data needed for option display of
      - face
      - ship
      - icon
      - text
    """

    def __init__(self, left, top, tag_prefix, items, 
                 text=None, face=None, ship=None, icon=None, image=None, 
                 title=None,  background=None, title_background=None,
                 select=False, multi=False, item_height=5, convert_value=None) -> None:
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
        self.title = title
        self.cur = 0
        self.bottom = top+40
        self.right = left+33
        self.items = items
        self.text = text
        self.face = face
        self.ship = ship
        self.image = image
        self.select_color = "#bbb3"
        self.click_color = "black"
        self.icon = icon
        self.select = select
        self.multi= multi
        self.slot_count = 0
        self.item_height = item_height # in percent
        self.square_width_percent = 0
        self.slots =[]
        self.selected = set()
        self.background=background
        self.title_background=title_background
        self.convert_value = convert_value


    def present(self, event):
        """ present

        builds/manages the content of the widget
     
        :param sim: simulation
        :type sim: Artemis Cosmos simulation
        :param CID: Client ID
        :type CID: int
        """
        CID = event.client_id
        
        aspect_ratio = get_client_aspect_ratio(CID) 
        #print(f"list box {aspect_ratio.x} {aspect_ratio.y} ")
        if aspect_ratio.x == 0 or aspect_ratio.y == 1:
            square_ratio = 1.0
        elif aspect_ratio.x > aspect_ratio.y:
            square_ratio = aspect_ratio.y / aspect_ratio.x
        else:
            square_ratio = aspect_ratio.x / aspect_ratio.y
        # One percent in pixels
        square_width_percent = square_ratio * self.item_height
        square_height_percent = self.item_height
        
        # force redraw of on size change
        if square_width_percent != self.square_width_percent:
            self.gui_state = "redraw"
            #print("Changed listbox ratio")
            self.square_width_percent = square_width_percent

        # Not sure this is needed, 
        # Plus we don't know when the gui was cleared
        # if this is needed then a bigger solution in general is needed
        # that resets this state when the page state is reset
        #
        # if self.gui_state == "presenting":
        #    return
           
        
        if self.items is None:
            sbs.send_gui_text(
                    CID, f"{self.tag_prefix}error", f"text:Error no items;", self.left, self.top, self.right, self.top+5)
            return

        left = self.left
        top = self.top
        if self.title is not None:
            title = self.title()
            if self.title_background is not None:
                props = f"image:smallWhite; color:{self.title_background};" # sub_rect: 0,0,etc"
                sbs.send_gui_image(CID, 
                    f"{self.tag_prefix}tbg", props,
                    self.left, self.top, self.right, top+self.item_height)
            sbs.send_gui_text(
                    CID, f"{self.tag_prefix}title", f"{title}",self.left, top, self.right, top+self.item_height)
            top += self.item_height

        if self.background is not None:
            props = f"image:smallWhite; color:{self.background};" # sub_rect: 0,0,etc"
            sbs.send_gui_image(CID, 
                f"{self.tag_prefix}bg", props,
                self.left, self.top, self.right, self.bottom)


        if len(self.items)==0:
            return
        
        cur = self.cur
        max_slot = (self.bottom-top)/self.item_height
        slot_count = len(self.items)-max_slot
        if slot_count > 0:
            self.slot_count = slot_count
            sbs.send_gui_slider(CID, f"{self.tag_prefix}cur", int(slot_count-self.cur +0.5), f"low:0.0; high: {(slot_count+0.5)}; show_number:no",
                        (self.right-1), top,
                        self.right, self.bottom)
        slot= 0
        self.slots =[]

    
        
        while top+5 <= self.bottom:
            if cur >= len(self.items):
                break
            item = self.items[cur]
            # track what item is in what slot
            self.slots.append(cur)
            if self.icon is not None:
                icon_to_display = self.icon(item)
                sbs.send_gui_icon(CID,  f"{self.tag_prefix}icon:{slot}", icon_to_display,
                    left, top,
                    left+square_width_percent, top+square_height_percent )
                left += square_width_percent
            if self.image is not None:
                image_to_display = self.image(item)
                if image_to_display is not None:
                    props = layout.split_props(image_to_display, "image")
                    rel_file = os.path.relpath(props["image"].strip(), fs.get_artemis_data_dir()+"\\graphics")
                    props["image"] = rel_file
                    image_to_display = layout.merge_props(props)
                    
                    sbs.send_gui_image(CID,f"{self.tag_prefix}image:{slot}", image_to_display, 
                        # cell_left, cell_top, cell_right, cell_bottom,
                        left, top, self.left+square_width_percent,  top+square_height_percent
                    )
                    left += square_width_percent
            if self.ship: 
                ship_to_display = self.ship(item)
                if "hull_tag:" not in ship_to_display:
                    ship_to_display = "hull_tag:"+ship_to_display

                sbs.send_gui_3dship(CID,  f"{self.tag_prefix}ship:{slot}", ship_to_display,
                    left, top,
                    left+square_width_percent, top+square_height_percent )
                left += square_width_percent
            if self.face: 
                face = self.face(item)
                sbs.send_gui_face(CID, f"{self.tag_prefix}face:{slot}",  face,
                    left, top,
                    left+square_width_percent, top+square_height_percent )
                left += square_width_percent
            text = ""
            if self.text:
                text = self.text(item)
                if "text:" not in text:
                    text = f"text:{text};justify:center;"
            sbs.send_gui_text(
                    CID, f"{self.tag_prefix}name:{slot}", text,
                        left, top, self.right, top+self.item_height)
            if self.select or self.multi:
                #print(f"{cur} selected {1 if cur in self.selected else 0}")
                # sbs.send_gui_checkbox(
                #     CID, f"{self.tag_prefix}name:{slot}", f"state: {'on' if cur in self.selected else 'off'}; {text}",
                #         left, top, self.right-1.5, top+self.item_height)
                myright = left
                if cur in self.selected:
                    myright = self.right
                props = f"image:smallWhite; color:{self.select_color};" # sub_rect: 0,0,etc"
                sbs.send_gui_image(CID, 
                    f"{self.tag_prefix}bk:{slot}", props,
                    left, 
                    top, 
                    myright,
                    top+self.item_height)
                sbs.send_gui_clickregion(CID, 
                    #text = self.text(item)
                    f"{self.tag_prefix}click:{slot}", f"font:gui-2;color:blue;{text}",
                    left, 
                    top, 
                    self.right,
                    top+self.item_height)
            #else:
            
            top += self.item_height
            cur += 1
            slot+=1
            
            left = self.left
        
        self.gui_state = "presenting"

    def get_image_size(self, file):
        try:
            with open(file+".png", 'rb') as f:
                data = f.read(26)
                # Chck if is png
                #if (data[:8] == '\211PNG\r\n\032\n'and (data[12:16] == 'IHDR')):
                w, h = struct.unpack('>LL', data[16:24])
                return w,h
        except Exception:
            return 0,0
    def on_message(self, event):
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
                value = int(-event.sub_float+self.slot_count+0.5)
                if value != self.cur:
                    self.cur = value
                    self.gui_state = "redraw"
                    self.present(event)
                return True
        if message_tag.startswith('click:'):
            slot = int(message_tag[6:])
            # could be an old message with a different sized list box
            if slot < 0 or slot >= len(self.slots):
                return
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
            self.present(event)

                
        return False
    def get_selected(self):
        ret = []
        for item in self.selected:
            ret.append(self.items[item])
        return ret
    
    def get_value(self):
        ret = []
        if self.convert_value:
            for item in self.selected:
                ret.append(self.convert_value(self.items[item]))
        else:
            ret = self.get_selected()

        if self.multi:
            return ret
        elif len(ret):
            return ret[0]
        else:
            return None
    
    def set_value(self, value):
        self.selected = []
        i = 0
        for item in self.items:
            if self.convert_value:
                v = self.convert_value(item)
                if v == value:
                    self.selected.append(i)
            elif item == value:
                self.selected.append(i)
            i+=1
    
    def update(self, props):
        pass


#list_box_control(ships, text=lambda ship: ship.comms_id, ship=lambda ship: ship.art_id)



def list_box_control(items, text=None, face=None, ship=None, icon=None, image=None, 
                     title=None, background=None, title_background=None,
                     select=False, multi=False, item_height=5,
                     convert_value=None):
    return Listbox(0, 0, "mast", items, text=text, face=face, ship=ship, 
                   icon = icon, image = image, 
                   title=title, background=background, title_background=title_background,
                   select=select, multi=multi, item_height=item_height,
                   convert_value=convert_value)
