from .inventory import get_inventory_value, set_inventory_value
from ..helpers import FrameContext

TICK_PER_SECONDS = 30
def set_timer(id_or_obj, name, seconds=0, minutes =0):
    seconds += minutes*60
    seconds *= TICK_PER_SECONDS
    seconds += FrameContext.context.sim.time_tick_counter
    set_inventory_value(id_or_obj, f"__timer__{name}", seconds)

def is_timer_set(id_or_obj, name):
    return get_inventory_value(id_or_obj, f"__timer__{name}", None) is not None


def is_timer_finished(id_or_obj, name):
    target = get_inventory_value(id_or_obj, f"__timer__{name}")
    if target is None or target == 0:
        return True
    now = FrameContext.context.sim.time_tick_counter
    if now > target:
        return True
    return False

def is_timer_set_and_finished(id_or_obj, name):
    target = get_inventory_value(id_or_obj, f"__timer__{name}")
    if target is None or target == 0:
        return False
    now = FrameContext.context.sim.time_tick_counter
    if now > target:
        return True
    return False


def clear_timer(id_or_obj, name):
    set_inventory_value(id_or_obj, f"__timer__{name}", None)

def start_counter(id_or_obj, name):
    set_inventory_value(id_or_obj, f"__counter__{name}", FrameContext.context.sim.time_tick_counter)

def get_counter_elapsed_seconds(id_or_obj, name):
    start = get_inventory_value(id_or_obj, f"__counter__{name}")
    now =  FrameContext.context.sim.time_tick_counter
    if start is None:
        return None
    return int((now-start) / TICK_PER_SECONDS)
    

def clear_counter(id_or_obj, name):
    set_inventory_value(id_or_obj, f"__counter__{name}", None)
