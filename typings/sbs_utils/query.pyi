from sbs_utils.engineobject import CloseData
from sbs_utils.engineobject import EngineObject
from sbs_utils.engineobject import SpawnData
from sbs_utils.spaceobject import SpaceObject
def broad_test (x1: float, z1: float, x2: float, z2: float, broad_type=-1):
    ...
def clear_target (sim, chasers: set | int | sbs_utils.engineobject.CloseData | sbs_utils.engineobject.SpawnData):
    """Clear the target
    
    :param sim: The simulation
    :type sim: Artemis Cosmos simulation"""
def closest (self, the_set, max_dist=None, filter_func=None) -> sbs_utils.engineobject.CloseData:
    ...
def closest_list (source: int | sbs_utils.engineobject.CloseData | sbs_utils.engineobject.SpawnData | sbs_utils.spaceobject.SpaceObject, the_set, max_dist=None, filter_func=None) -> list:
    ...
def closest_object (self, the_set, max_dist=None, filter_func=None) -> sbs_utils.spaceobject.SpaceObject:
    ...
def get_dedicated_link (so, link):
    ...
def get_inventory_value (so, link):
    ...
def has_inventory (role: str):
    ...
def has_link (role: str):
    ...
def inventory_set (link_source, link_name: str):
    ...
def inventory_value (link_source, link_name: str):
    ...
def link (set_holder, link, set_to):
    ...
def linked_to (link_source, link_name: str):
    ...
def object_exists (sim, so_id):
    ...
def random_object (the_set):
    ...
def random_object_list (the_set, count=1):
    ...
def role (role: str):
    ...
def set_dedicated_link (so, link, to):
    ...
def set_inventory_value (so, link, to):
    ...
def target (sim, set_or_object, target_id, shoot: bool = True):
    """Set the item to target
    :param sim: The simulation
    :type sim: Artemis Cosmos simulation
    :param other_id: the id of the object to target
    :type other_id: int
    :param shoot: if the object should be shot at
    :type shoot: bool"""
def target_pos (sim, chasers: set | int | sbs_utils.engineobject.CloseData | sbs_utils.engineobject.SpawnData, x: float, y: float, z: float):
    """Set the item to target
    
    :param sim: The simulation
    :type sim: Artemis Cosmos simulation
    :param other_id: the id of the object to target
    :type other_id: int
    :param shoot: if the object should be shot at
    :type shoot: bool"""
def to_id (other: sbs_utils.engineobject.EngineObject | sbs_utils.engineobject.CloseData | int):
    ...
def to_id_list (the_set):
    ...
def to_list (other: sbs_utils.engineobject.EngineObject | sbs_utils.engineobject.CloseData | int):
    ...
def to_object (other: sbs_utils.engineobject.EngineObject | sbs_utils.engineobject.CloseData | int):
    ...
def to_object_list (the_set):
    ...
def to_py_object_list (the_set):
    ...
def to_set (other: sbs_utils.engineobject.EngineObject | sbs_utils.engineobject.CloseData | int):
    ...
def unlink (set_holder, link, set_to):
    ...
