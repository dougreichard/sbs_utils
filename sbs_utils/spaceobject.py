from __future__ import annotations
from typing import Callable
import sbs
from enum import IntEnum
from .agent import Agent, SpawnData
from .helpers import FrameContext
from .procedural import ship_data as SHIP_DATA


class TickType(IntEnum):
    PASSIVE = 0,
    TERRAIN = 0,
    ACTIVE = 1,
    NPC = 1,
    PLAYER = 2,
    UNKNOWN = -1,
    ALL = -1


class SpaceObject(Agent):
    # roles : Stuff = Stuff()
    # _has_inventory : Stuff = Stuff()
    # has_links : Stuff = Stuff()
    # all = {}
    # removing = set()

    def __init__(self):
        super().__init__()
        self._name = ""
        self._side = ""
        self._art_id = ""
        self.spawn_pos = sbs.vec3(0,0,0)
        self.tick_type = TickType.UNKNOWN
        self._data_set = None
        self._engine_object = None
    
    @property
    def is_player(self):
        return self.tick_type == TickType.PLAYER

    @property
    def is_npc(self):
        return self.tick_type == TickType.ACTIVE

    @property
    def is_terrain(self):
        return self.tick_type == TickType.PASSIVE

    @property
    def is_active(self):
        return self.tick_type == TickType.ACTIVE

    @property
    def is_passive(self):
        return self.tick_type == TickType.PASSIVE


    def get_space_object(self):
        """ Gets the simulation space object

        :return: The simulation space object
        :rtype: The simulation space_object
        """

        return FrameContext.context.sim.get_space_object(self.id)

    def get_engine_object(self):
        """ Gets the simulation space object

        :return: The simulation space object
        :rtype: The simulation space_object
        """
        return FrameContext.context.sim.get_space_object(self.id)

    
    

    def debug_mark_loc(sim,  x: float, y: float, z: float, name: str, color: str):
        """ Adds a nav point to the location passed if debug mode is on

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
            return FrameContext.context.sim.add_navpoint(x, y, z, name, color)
        return None

    def debug_remove_mark_loc(name: str):
        if SpaceObject.debug:
            return FrameContext.context.sim.delete_navpoint_by_name(name)
        return None

    def log(s: str):
        if SpaceObject.debug:
            print(s)

    def space_object(self):
        """ get the simulation's space object for the object

        :return: simulation space object
        :rtype: simulation space object
        """
        return self._engine_object
        # return FrameContext.context.sim.get_space_object(self.id)

    def set_side(self, side):
        """ Get the side of the object

        :return: side
        :rtype: str
        """
        so = self.space_object()
        self._side = side
        self.update_comms_id()
        if so is not None:
            so._side = side

    def set_name(self, name):
        """ Get the name of the object
        :return: name
        :rtype: str
        """
        so = self.space_object()
        self._name = name
        self.update_comms_id()
        if so is None:
            return
        blob = so.data_set
        return blob.set("name_tag", name, 0)
    
    def set_art_id(self, art_id):
        """ Get the name of the object

        :return: name
        :rtype: str
        """
        so = self.space_object()
        so.data_tag = art_id
        self._art_id = art_id

    def update_comms_id(self):
        """ Updates the comms ID when the name or side has changed
        :return: this is name or name(side)
        :rtype: str
        """

        if (self.side != ""):
            self._comms_id = f"{self.name} ({self.side})"
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
    def comms_id(self: SpaceObject) -> str:
        """str, cached version of comms_id"""
        return self._comms_id
    
    @property
    def art_id(self: SpaceObject) -> str:
        """str, cached version of art_id"""
        return self._art_id

    @art_id.setter
    def art_id(self: SpaceObject, value: str):
        self._art_id = value
        self.space_object().art_id = value



class MSpawn:
    def spawn_common(self, obj, x, y, z, name, side, art_id):
        self.spawn_pos = sbs.vec3(x,y,z)
        self._engine_object = obj

        FrameContext.context.sim.reposition_space_object(obj, x, y, z)
        self.add()
        self.add_role(self.__class__.__name__)
        self.add_role("__space_spawn__")
        self.add_role("__SPACE_OBJECT__")
        #
        # Add default roles
        #
        ship_data = SHIP_DATA.get_ship_data_for(art_id)
        if ship_data:
            roles = ship_data.get("roles", None)
            if roles:
                self.add_role(roles)


        blob = obj.data_set
        self._data_set = blob

        if name is not None:
            self._name = name
            blob.set("name_tag", name, 0)

        if side is not None:
            if isinstance(side, str):
                roles = side.split(",")
            else:
                roles = side
            side = roles[0].strip()
            if side != "#":
                obj.side = side
                self._side = side
            self.update_comms_id()
            for role in roles:
                self.add_role(role)
        else:
            self._comms_id = name if name is not None else f""
        
        return blob


class MSpawnPlayer(MSpawn):
    def _make_new_player(self, behave, data_id):
        self.id = FrameContext.context.sim.make_new_player(behave, data_id)
        self.tick_type = TickType.PLAYER
        return FrameContext.context.sim.get_space_object(self.id)

    def _spawn(self, x, y, z, name, side, art_id):
        # playerID will be a NUMBER, a unique value for every space object that you create.
        ship = self._make_new_player("behav_playership", art_id)
        blob = self.spawn_common(ship, x, y, z, name, side, art_id)
        self.add_role("__PLAYER__")
        self._art_id = art_id
        return SpawnData(self.id, ship, blob, self)

    def spawn(self, x, y, z, name, side, art_id):
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
        return self._spawn(x, y, z, name, side, art_id)

    def spawn_v(self, v, name, side, art_id):
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
        return self.spawn(v.x, v.y, v.z, name, side, art_id)


class MSpawnActive(MSpawn):
    """
    Mixin to add Spawn as an Active
    """

    def _make_new_active(self, behave, data_id):
        self.id = FrameContext.context.sim.make_new_active(behave, data_id)
        self.tick_type = TickType.ACTIVE
        return self.get_space_object()

    def _spawn(self, x, y, z, name, side, art_id, behave_id):
        ship = self._make_new_active(behave_id, art_id)
        blob = self.spawn_common(ship, x, y, z, name, side, art_id)
        self._art_id = art_id
        self.add_role("__NPC__")
        return SpawnData(self.id, ship, blob, self)

    def spawn(self, x, y, z, name, side, art_id, behave_id):
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
        return self._spawn(x, y, z, name, side, art_id, behave_id)

    def spawn_v(self, sim, v, name, side, art_id, behave_id):
        """ Spawn a new Active Object e.g. npc, station

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
        return self._spawn( v.x, v.y, v.z, name, side, art_id, behave_id)


class MSpawnPassive(MSpawn):
    """
    Mixin to add Spawn as an Passive
    """

    def _make_new_passive(self, behave, data_id):
        self.id = FrameContext.context.sim.make_new_passive(behave, data_id)
        self.tick_type = TickType.PASSIVE
        return self.get_space_object()

    def _spawn(self, x, y, z, name, side, art_id, behave_id):
        ship = self._make_new_passive(behave_id, art_id)
        blob = self.spawn_common(ship, x, y, z, name, side, art_id)
        self._art_id = art_id
        self.add_role("__TERRAIN__")
        return SpawnData(self.id, ship, blob, self)

    def spawn(self, x, y, z, name, side, art_id, behave_id):
        """ Spawn a new passive object e.g. Asteroid, etc.

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
        return self._spawn(x, y, z, name, side, art_id, behave_id)

    def spawn_v(self, v, name, side, art_id, behave_id):
        """ Spawn a new passive object e.g. asteroid, etc.

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
        return self._spawn(v.x, v.y, v.z, name, side, art_id, behave_id)

