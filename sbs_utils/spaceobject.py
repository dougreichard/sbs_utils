from __future__ import annotations
from typing import Callable
import sbs
from random import randrange, choice, choices


#class SpaceObject:
#    pass

class SpawnData:
    id : int
    engine_object : any
    blob: any
    py_object: SpaceObject

    def __init__(self, id, obj, blob, py_obj) -> None:
        self.id = id
        self.engine_object = obj
        self.blob = blob
        self.py_object = py_obj

class CloseData:
    id: int
    py_object: SpaceObject
    distance: float

    def __init__(self, other_id, other_obj, distance) -> None:
        self.id = other_id
        self.py_object = other_obj
        self.distance = distance

class SpaceObject:
    ids = {'all':{}}
    debug = True
    removing =set()

    def __init__(self):
        self._name = ""
        self._side = ""

    def destroyed(self):
        self.remove()

    def get_id(self):
        return self.id


    def _add(id, obj):
        SpaceObject.ids['all'][id] = obj

    def _remove(id):
        return SpaceObject._remove_every_role(id)

    def _add_role(role, id, obj):
        if role not in SpaceObject.ids:
            SpaceObject.ids[role]={}
        SpaceObject.ids[role][id] = obj

    def add_role(self, role: str):
        """ Add a role to the space object

        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        """
        SpaceObject._add_role(role, self.id, self)

    def _remove_role(role, id):
        if SpaceObject.ids.get(role) is not None:
            SpaceObject.ids[role].pop(id, None)


    def remove_role(self, role: str):
        """ Remove a role from the space object

        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        """

        SpaceObject._remove_role(role, self.id)

    def has_role(self, role):
        """ check if the object has a role

        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool
        """

        if role not in SpaceObject.ids:
            return False

        if isinstance(role, str):
            return SpaceObject.ids[role].get(self.id) is not None
        try:
            for r in role:
                if SpaceObject.ids[r].get(self.id) is not None:
                    return True
        except:
            return False
        return False


    def _remove_every_role(id):
        for role in SpaceObject.ids:
            SpaceObject._remove_role(role, id)

    def get_roles(self, id):
        roles = []
        for role in SpaceObject.ids:
            if self.has_role(role):
                roles.append(role)
        return roles

    def get_objects_with_role(role):
        if SpaceObject.ids.get(role):
            # return a list so you can remove while iterating
            return list(SpaceObject.ids.get(role).values())
        return []

    def get_role_set(role):
        if SpaceObject.ids.get(role):
            return set(SpaceObject.ids.get(role).keys())
        return set()


    ############### LINKS ############
    def _add_link(self, link_name: str, id : int):
        if not hasattr(self, "links"):
            self.links = {}
        if link_name not in self.links:
            self.links[link_name]=set()
        self.links[link_name].add(id)

    def add_link(self, link_name: str, other: SpaceObject | CloseData | int):
        """ Add a link to the space object. Links are uni-directional

        :param role: The role/link name to add e.g. spy, pirate etc.
        :type id: str
        """
        id = SpaceObject.resolve_id(other)

        self._add_link(link_name, id)

    def _remove_link(self, role, id):
        if self.links.get(role) is not None:
            self.links[role].remove(id)


    def remove_link(self, link_name: str, other: SpaceObject | CloseData | int):
        """ Remove a role from the space object

        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        """
        id = SpaceObject.resolve_id(other)

        self._remove_link(link_name, id)

    def has_link_to(self, link_name: str | list[str], other: SpaceObject| CloseData |int):
        """ check if the object has a role

        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool
        """
        id = SpaceObject.resolve_id(other)
            
        if link_name not in self.links:
            return False

        if isinstance(link_name, str):
            return  id in self.links[link_name]
        try:
            for r in link_name:
                if id in self.links[link_name]:
                    return True
        except:
            return False
        return False


    def _remove_every_link(self, other: SpaceObject | CloseData| int):
        id = SpaceObject.resolve_id(other)
        for role in self.links:
            self._remove_link(role, id)

    def get_links(self, other: SpaceObject| CloseData | int):
        links = []
        id = SpaceObject.resolve_id(other)
        for link_name in self.links.keys():
            if self.has_link_to(link_name, id):
                links.append(link_name)
        return links

    def resolve_id(other: SpaceObject | CloseData | int ):
        id = other
        if isinstance(other, SpaceObject):
            id = other.id
        elif isinstance(other, CloseData):
            id = other.id
        elif isinstance(other, SpawnData):
            id = other.id
        return id

    def get_objects_with_link(self, link_name):
        the_set = self.links.get(link_name)
        if self.links.get(link_name):
            # return a list so you can remove while iterating
            return [ SpaceObject.get(x) for x in the_set]
        return []

    def get_link_set(self, link_name):
        return self.links.get(link_name, set())

    def get_objects_from_set(the_set):
        return [ SpaceObject.get(x) for x in the_set]


    ####################################
    def get(id):
        o = SpaceObject.ids['all'].get(id)
        if o is None:
            return None
        return o

    def get_as(id, cls):
        o = SpaceObject.ids['all'].get(id)
        if o is None:
            return None
        if o.__class__ != cls:
            return None
        return o

    def py_class():
        return __class__

    def add(self):
        """ Add the object to the system, called by spawn normally
        """
        SpaceObject._add(self.id, self)

    def remove(self):
        """ remove the object to the system, called by destroyed normally
        """
        SpaceObject._remove(self.id)

    def get_space_object(self, sim):
        """ Gets the simulation space object

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :return: The simulation space object
        :rtype: The simulation space_object
        """

        return sim.get_space_object(self.id)

    
    def all(roles:str, linked_object: SpaceObject|None = None, filter_func=None):
        roles = roles.split(",\*")
        ret = set()
        if linked_object:
            for role in roles:
                objects = linked_object.get_objects_with_link(role)
                ret |= set(objects)
        else:
            for role in roles:
                objects = SpaceObject.get_objects_with_role(role)
                ret |= set(objects)

        items = list(ret)
        if filter_func is not None:
            items = filter(filter_func, items)

        return items

    def find_close_list(self, sim, roles=None, max_dist=None, filter_func=None, linked = False)-> list[CloseData]:
        """ Finds a list of matching objects 

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param roles: Roles to looks for can also be class name
        :type roles: str or List[str] 
        :param max_dist: Max distance to search (faster)
        :type max_dist: float
        :param filter_func: Called to test each object to filter out non matches
        :type filter_func: 
        :return: A list of close object
        :rtype: List[CloseData]
        """
        items = SpaceObject.all(roles, self if linked else None, filter_func)
        return self.find_close_filtered_list(sim, items, max_dist)

    def find_close_filtered_list(self, sim, items, max_dist=None)-> list[CloseData]:
        ret = []
        test = max_dist

        for other_obj in items:
            # if this is self skip
            if other_obj.id == self.id:
                continue

            # test distance
            test = sbs.distance_id(self.id, other_obj.id)
            if max_dist is None:
                ret.append(CloseData(other_obj.id, other_obj, test))
                continue

            if test < max_dist:
                ret.append(CloseData(other_obj.id, other_obj, test))

        return ret

    def find_closest(self, sim, roles=None, max_dist=None, filter_func=None, linked:bool = False) -> CloseData:
        """ Finds the closest object matching the criteria

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param roles: Roles to looks for can also be class name
        :type roles: str or List[str] 
        :param max_dist: Max distance to search (faster)
        :type max_dist: float
        :param filter_func: Called to test each object to filter out non matches
        :type filter_func: function that takes ID
        :return: A list of close object
        :rtype: CloseData
        """
        dist = None
        # list of close objects
        items = self.find_close_list(sim, roles, max_dist, filter_func, linked )
        # Slightly inefficient 
        # Maybe this should be a filter function?
        for other in items:
            test = sbs.distance_id(self.id, other.id)
            if dist is None:
                close_obj = other
                dist = test
            elif test < dist:
                close_obj = other
                dist = test

        return close_obj

    def target_closest(self, sim, roles=None, max_dist=None, filter_func=None, shoot: bool = True, linked: bool = True):
        """ Find and target the closest object matching the criteria

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param roles: Roles to looks for can also be class name
        :type roles: str or List[str] 
        :param max_dist: Max distance to search (faster)
        :type max_dist: float
        :param filter_func: Called to test each object to filter out non matches
        :type filter_func: function
        :param shoot: if the target should be shot at
        :type shoot: bool
        :return: A list of close object
        :rtype: CloseData
        """
        close = self.find_closest(sim, roles, max_dist, filter_func, linked)
        if close.id is not None:
            self.target(sim, close.id, shoot)
        return close

    def target(self, sim, other_id: int, shoot: bool = True):
        """ Set the item to target

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param other_id: the id of the object to target
        :type other_id: int
        :param shoot: if the object should be shot at
        :type shoot: bool
        """
        SpaceObject.resolve_id(other_id)
        other = sim.get_space_object(other_id)
        
        if other:
            data = {
            "target_pos_x": other.pos.x,
            "target_pos_y": other.pos.y,
            "target_pos_z": other.pos.z,
            "target_id": 0
            }
            if shoot:
                data["target_id"] = other.unique_ID
            self.update_engine_data(sim, data)

    def target_pos(self, sim, x:float, y:float, z:float):
        """ Set the item to target

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param other_id: the id of the object to target
        :type other_id: int
        :param shoot: if the object should be shot at
        :type shoot: bool
        """
        data = {
            "target_pos_x": x,
            "target_pos_y": y,
            "target_pos_z": z,
            "target_id": 0
            }
        self.update_engine_data(sim, data)

    def find_closest_nav(self, sim, nav=None, max_dist=None, filter_func=None) -> CloseData:
        """ Finds the closest object matching the criteria

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param roles: Roles to looks for can also be class name
        :type nav: str or List[str] 
        :param max_dist: Max distance to search (faster)
        :type max_dist: float
        :param filter_func: Called to test each object to filter out non matches
        :type filter_func: function that takes ID
        :return: A list of close object
        :rtype: CloseData
        """
        close_id = None
        close_obj = None
        dist = max_dist

        ###### TODO USe boardtest if max_dist used

        items = []
        if type(nav) == str:
            items.append(nav)
        else:
            items.extend(nav)
            
        if filter_func is not None:
            items = filter(filter_func, items)

        for nav in items:
            
            test = sbs.distance_to_navpoint(self.id, nav)
            if dist is None:
                close_id = nav
                close_obj = nav
                dist = test
            elif test < dist:
                close_id = nav
                close_obj = nav
                dist = test

        return CloseData(close_id, close_obj, dist)

    def target_closest_nav(self, sim, nav=None, max_dist=None, filter_func=None, shoot: bool = True):
        found = self.find_closest_nav(sim,nav,max_dist, filter_func)
        if found.id is not None:
            nav_object = sim.get_navpoint_by_name(found.id)
            self.target_pos(nav_object.pos.x, nav_object.pos.y,nav_object.pos.z)
        return found

    def update_engine_data(self,sim, data):
        this = sim.get_space_object(self.id)
        if this is None:
            # Object is destroyed
            return
        blob = this.data_set
        for (key, value) in data.items():
            if type(value) is tuple:
                blob.set(key, value[0], value[1])
            else:
                blob.set(key, value)

    def get_engine_data(self,sim, key, index=0):
        this = sim.get_space_object(self.id)
        if this is None:
            # Object is destroyed
            return
        blob = this.data_set
        return blob.get(key, index)
    
    def set_engine_data(self,sim, key, value, index=0):
        this = sim.get_space_object(self.id)
        if this is None:
            # Object is destroyed
            return
        blob = this.data_set
        blob.set(key, value, index)

    def get_engine_data_set(self,sim):
        this = sim.get_space_object(self.id)
        if this is None:
            # Object is destroyed
            return None
        return  this.data_set


    def clear_target(self, sim):
        """ Clear the target

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        """
        this = sim.get_space_object(self.id)
        self.update_engine_data(sim, {
            "target_pos_x": this.pos.x,
            "target_pos_y": this.pos.y,
            "target_pos_z": this.pos.z,
            "target_id": 0
        })
        

    def debug_mark_loc(sim,  x: float, y: float, z: float, name: str, color: str):
        """ Adds a nav point to the location passed if debug mode is on

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param x: x location
        :type x: float
        :param y: y location
        :type y: float
        :param z: z location
        :type z: float
        :param name: name of the navpoint
        :type name: str
        :param color: color of the navpoint
        :type color: str
        """
        if SpaceObject.debug:
            return sim.add_navpoint(x, y, z, name, color)
        return None

    def debug_remove_mark_loc(sim, name: str):
        if SpaceObject.debug:
            return sim.delete_navpoint_by_name(name)
        return None

    def log(s: str):
        if SpaceObject.debug:
            print(s)

    def space_object(self, sim):
        """ get the simulation's space object for the object

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :return: simulation space object
        :rtype: simulation space object
        """
        return sim.get_space_object(self.id)

    def set_side(self, sim, side):
        """ Get the side of the object

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :return: side
        :rtype: str
        """
        so = self.space_object(sim)
        self.side = side
        self.update_comms_id()
        if so is not None:
            so.side = side

        
    def set_name(self, sim, name):
        """ Get the name of the object

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :return: name
        :rtype: str
        """
        so = self.space_object(sim)
        self.name = name
        self.update_comms_id()
        if so is None:
            return
        blob = so.data_set
        return blob.set("name_tag", name, 0)

    def update_comms_id(self):
        """ Updates the comms ID when the name or side has changed
        :return: this is name or name(side)
        :rtype: str
        """
        
        if (self.side != ""):
            self._comms_id = f"{self.name}({self.side})"
        else:
            self._comms_id = self.name

    @property
    def name(self: SpaceObject) -> str:
        """str, cached version of comms_id"""
        return self._name

    @property
    def side(self: SpaceObject) -> str:
        """str, cached version of comms_id"""
        return self._side

    @property
    def comms_id (self: SpaceObject) -> str:
        """str, cached version of comms_id"""
        return self._comms_id



class MSpawn:
    def spawn_common(self, sim, obj, x,y,z,name, side):
        sim.reposition_space_object(obj, x, y, z)
        self.add()
        self.add_role(self.__class__.__name__)
        blob = obj.data_set
        if side is not None:
            self._comms_id= f"{name}({side})" if name is not None else f"{side}{self.id}"
            obj._side = side
            self.add_role(side)
        else:
            self._comms_id= name if name is not None else f""
        if name is not None:
            self._name = name
            blob.set("name_tag", name, 0)
        
        return blob

class MSpawnPlayer(MSpawn):
    def _make_new_player(self, sim, behave, data_id):
        self.id = sim.make_new_player(behave, data_id)
        self.is_player = True
        return sim.get_space_object(self.id)

    def _spawn(self, sim, x, y, z, name, side, art_id):
        # playerID will be a NUMBER, a unique value for every space object that you create.
        ship = self._make_new_player(sim, "behav_playership", art_id)
        blob = self.spawn_common(sim, ship, x,y,z,name, side)
        self.add_role("__PLAYER__")
        return SpawnData(self.id, ship, blob, self)


    def spawn(self, sim, x, y, z, name, side, art_id):
        """ Spawn a new player

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param x: x location
        :type x: float
        :param y: y location
        :type y: float
        :param z: z location
        :type z: float
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        :param behave_id: the simulation behavior
        :type behave_id: str
        :return: spawn data
        :rtype: SpawnData
        """
        return self._spawn(sim, x, y, z, name, side, art_id)

    def spawn_v(self, sim, v, name, side, art_id):
        """ Spawn a new player

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param v: location
        :type v: Vec3
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        
        :return: spawn data
        :rtype: SpawnData
        """
        return self.spawn(sim, v.x, v.y, v.z, name, side, art_id)

class MSpawnActive(MSpawn):
    """
    Mixin to add Spawn as an Active
    """
    def _make_new_active(self, sim,  behave, data_id):
        self.id = sim.make_new_active(behave, data_id)
        self.is_player = False
        return self.get_space_object(sim)

    def _spawn(self, sim, x, y, z, name, side, art_id, behave_id):
        ship = self._make_new_active(sim, behave_id, art_id)
        blob = self.spawn_common(sim, ship, x,y,z,name, side)
        return SpawnData(self.id, ship, blob, self)

    def spawn(self, sim, x, y, z, name, side, art_id, behave_id):
        """ Spawn a new active object e.g. npc, station

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param x: x location
        :type x: float
        :param y: y location
        :type y: float
        :param z: z location
        :type z: float
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        :param behave_id: the simulation behavior
        :type behave_id: str

        :return: spawn data
        :rtype: SpawnData
        """
        return self._spawn(sim, x, y, z, name, side, art_id, behave_id)

    def spawn_v(self, sim, v, name, side, art_id, behave_id):
        """ Spawn a new Active Object e.g. npc, station

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param v: location
        :type v: Vec3
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        :param behave_id: the simulation behavior
        :type behave_id: str

        :return: spawn data
        :rtype: SpawnData
        """
        return self._spawn(sim, v.x, v.y, v.z, name, side, art_id, behave_id)

class MSpawnPassive(MSpawn):
    """
    Mixin to add Spawn as an Passive
    """
    def _make_new_passive(self, sim, behave, data_id):
        self.id = sim.make_new_passive(behave, data_id)
        self.is_player = False
        return sim.get_space_object(self.id)

    def _spawn(self, sim, x, y, z, name, side, art_id, behave_id):
        ship = self._make_new_passive(sim, behave_id, art_id)
        blob = self.spawn_common(sim, ship, x,y,z,name, side)
        return SpawnData(self.id, ship, blob, self)

    def spawn(self, sim, x, y, z, name, side, art_id, behave_id):
        """ Spawn a new passive object e.g. Asteroid, etc.

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param x: x location
        :type x: float
        :param y: y location
        :type y: float
        :param z: z location
        :type z: float
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        :param behave_id: the simulation behavior
        :type behave_id: str

        :return: spawn data
        :rtype: SpawnData
        """
        return self._spawn(sim, x, y, z, name, side, art_id, behave_id)

    def spawn_v(self, sim, v, name, side, art_id, behave_id):
        """ Spawn a new passive object e.g. asteroid, etc.

        :param sim: The simulation
        :type sim: Artemis Cosmos simulation
        :param v: location
        :type v: Vec3
        :param name: name of object
        :type name: str
        :param side: name of object
        :type side: str
        :param art_id: art id
        :type art_id: str
        :param behave_id: the simulation behavior
        :type behave_id: str
        :return: spawn data
        :rtype: SpawnData
        """
        return self._spawn(sim, v.x, v.y, v.z, name, side, art_id, behave_id)


###################
## Set functions
def role(role:str):
    return SpaceObject.get_role_set(role)

def linked_to(link_name:str, link_source):
    link_source.get_link_set(link_name)

# Get the set of IDS of a broad test
def broad_test(x1:float,z1:float, x2:float,z2:float, broad_type=-1):
    obj_list = sbs.broad_test(x1, z1, x2, z2, broad_type)
    return {so.unique_ID for so in obj_list}


#######################
## Set resolvers
def closest_list(source: int|CloseData|SpawnData|SpaceObject, the_set, max_dist=None, filter_func=None)-> list[CloseData]:
    ret = []
    test = max_dist
    source_id = SpaceObject.resolve_id(source) 

    for other_id  in the_set:
        # if this is self skip
        if other_id == source_id:
            continue
        other_obj =SpaceObject.get(other_id)
        if filter_func is not None and not filter_func(other_obj):
            continue
        # test distance
        test = sbs.distance_id(source_id, other_id)
        if max_dist is None:
            ret.append(CloseData(other_id, other_obj, test))
            continue

        if test < max_dist:
            ret.append(CloseData(other_id, other_obj, test))

    return ret

def closest(self, the_set, max_dist=None, filter_func=None)-> CloseData:
    test = max_dist
    ret = None
    source_id = SpaceObject.resolve_id(self) 

    for other_id  in the_set:
        # if this is self skip
        if other_id == SpaceObject.resolve_id(self):
            continue
        other_obj =SpaceObject.get(other_id)
        if filter_func is not None and not filter_func(other_obj):
            continue

        # test distance
        test = sbs.distance_id(source_id, other_id)
        if max_dist is None:
            ret = CloseData(other_id, other_obj, test)
            max_dist=test
            continue
        elif test < max_dist:
            ret = CloseData(other_id, other_obj, test)
            continue

    return ret

def closest_object(self, sim, the_set, max_dist=None, filter_func=None)-> SpaceObject:
    ret = closest(self, sim, the_set, max_dist=None, filter_func=None)
    if ret:
        return ret.py_object

def random(the_set):
    rand_id = choice(tuple(the_set))
    return SpaceObject.get(rand_id)

def random_list(the_set, count=1):
    rand_id_list = choices(tuple(the_set), count)
    return [SpaceObject.get(x) for x in rand_id_list]

