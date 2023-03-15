class CloseData(object):
    """class CloseData"""
    def __init__ (self, other_id, other_obj, distance) -> 'None':
        """Initialize self.  See help(type(self)) for accurate signature."""
class EngineObject(object):
    """class EngineObject"""
    def __init__ (self):
        """Initialize self.  See help(type(self)) for accurate signature."""
    def _add (id, obj):
        ...
    def _remove (id):
        ...
    def _remove_every_inventory (self, data: 'object'):
        ...
    def _remove_every_link (self, other: 'EngineObject | CloseData | int'):
        ...
    def add (self):
        """Add the object to the system, called by spawn normally
                """
    def add_inventory (self, collection_name: 'str', data: 'object'):
        """Add a link to the space object. Links are uni-directional
        
        :param role: The role/link name to add e.g. spy, pirate etc.
        :type id: str"""
    def add_link (self, link_name: 'str', other: 'EngineObject | CloseData | int'):
        """Add a link to the space object. Links are uni-directional
        
        :param role: The role/link name to add e.g. spy, pirate etc.
        :type id: str"""
    def add_role (self, role: 'str'):
        """Add a role to the space object
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str"""
    def clear ():
        ...
    def destroyed (self):
        ...
    def get (id):
        ...
    def get_as (id, as_cls):
        ...
    def get_dedicated_link (self, link_name):
        ...
    def get_dedicated_link_object (self, link_name):
        ...
    def get_engine_data (self, sim, key, index=0):
        ...
    def get_engine_data_set (self, sim):
        ...
    def get_engine_object (self, sim):
        ...
    def get_id (self):
        ...
    def get_in_links (self, other: 'EngineObject | CloseData | int'):
        ...
    def get_inventory_in (self, data: 'object'):
        ...
    def get_inventory_list (self, collection_name):
        ...
    def get_inventory_objects (self, collection_name):
        ...
    def get_inventory_set (self, collection_name):
        ...
    def get_inventory_value (self, collection_name):
        ...
    def get_link_list (self, link_name):
        ...
    def get_link_objects (self, link_name):
        ...
    def get_link_set (self, link_name):
        ...
    def get_objects_from_set (the_set):
        ...
    def get_role_object (link_name):
        ...
    def get_role_objects (role):
        ...
    def get_role_set (role):
        ...
    def get_roles (self, id):
        ...
    def has_any_inventory (self, collection_name: 'str | list[str]'):
        ...
    def has_in_inventory (self, link_name: 'str | list[str]', data: 'object'):
        """check if the object has a role
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool"""
    def has_inventory_list (collection_name):
        ...
    def has_inventory_set (collection_name):
        ...
    def has_link_to (self, link_name: 'str | list[str]', other: 'EngineObject | CloseData | int'):
        """check if the object has a role
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool"""
    def has_links_list (collection_name):
        ...
    def has_links_set (collection_name):
        ...
    def has_role (self, role):
        """check if the object has a role
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool"""
    def py_class ():
        ...
    def remove (self):
        """remove the object to the system, called by destroyed normally
                """
    def remove_inventory (self, collection_name: 'str', data: 'object'):
        """Remove a role from the space object
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str"""
    def remove_link (self, link_name: 'str', other: 'EngineObject | CloseData | int'):
        """Remove a role from the space object
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str"""
    def remove_link_all (self, link_name: 'str'):
        """Remove a role from the space object
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str"""
    def remove_role (self, role: 'str'):
        """Remove a role from the space object
        
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str"""
    def resolve_id (other: 'EngineObject | CloseData | int'):
        ...
    def resolve_py_object (other: 'EngineObject | CloseData | int'):
        ...
    def set_dedicated_link (self, link_name: 'str', other: 'EngineObject | CloseData | int'):
        ...
    def set_engine_data (self, sim, key, value, index=0):
        ...
    def set_inventory_value (self, collection_name, value):
        ...
    def update_engine_data (self, sim, data):
        ...
class SpawnData(object):
    """class SpawnData"""
    def __init__ (self, id, obj, blob, py_obj) -> 'None':
        """Initialize self.  See help(type(self)) for accurate signature."""
class Stuff(object):
    """A Common class for Role, Links and Inventory"""
    def __init__ (self):
        """Initialize self.  See help(type(self)) for accurate signature."""
    def add_to_collection (self, collection, id):
        ...
    def clear (self):
        ...
    def collection_has (self, collection, id):
        """check if the object has a role
        :param role: The role to add e.g. spy, pirate etc.
        :type id: str
        :return: If the object has the role
        :rtype: bool"""
    def collection_list (self, collection):
        ...
    def collection_set (self, collection):
        ...
    def dedicated_collection (self, collection, id):
        ...
    def get_collections_in (self, id):
        ...
    def remove_collection (self, collection):
        ...
    def remove_every_collection (self, id):
        ...
    def remove_from_collection (self, collection, id):
        ...
