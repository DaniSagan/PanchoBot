from typing import Dict, Tuple, List, Any
from typing import List

import sqlite3
import importlib
import utils
from db.database import DataRow, DataTable, DataSet
from db.database import Database, DataSet
from jsonutils import JsonDeserializable


class PropertySource(JsonDeserializable):
    def __init__(self):
        self.name: str = ""
        self.type_: str = ""
        # self.src_table = ""  # type: str
        self.src_column: str = ""
        # self.referenced_table = ""  # type: str
        # self.referenced_column = ""  # type: str
        self.object_name: str = ""

    @classmethod
    def from_json(cls, json_object: Dict) -> 'PropertySource':
        res: PropertySource = PropertySource()
        res.name = json_object['name']
        res.type_ = json_object['type']
        # res.src_table = json_object['src_table']
        res.src_column = json_object['src_column']
        # res.referenced_table = json_object.get('referenced_table')
        # res.referenced_column = json_object.get('referenced_column')
        res.object_name = json_object.get('object_name')
        return res


class ObjectDefinition(JsonDeserializable):
    def __init__(self):
        self.object_name: str = ""
        self.object_id: str = ""
        self.table_name: str = ""
        self.property_sources: List[PropertySource] = []

    @classmethod
    def from_json(cls, json_object: Dict) -> 'ObjectDefinition':
        res: ObjectDefinition = ObjectDefinition()
        res.object_name = json_object['object_name']
        res.object_id = json_object['object_id']
        res.table_name = json_object['table_name']
        res.property_sources = [PropertySource.from_json(j) for j in json_object['property_sources']]
        return res


class ObjectProvider(JsonDeserializable):
    def __init__(self):
        self.object_definitions: List[ObjectDefinition] = []

    @classmethod
    def from_json(cls, json_object: Dict) -> 'ObjectProvider':
        res: ObjectProvider = ObjectProvider()
        res.object_definitions = [ObjectDefinition.from_json(j) for j in json_object['object_definitions']]
        return res

    def get_object_definition(self, object_name: str) -> ObjectDefinition:
        # object_name = object_type.__module__ + '.' + object_type.__name__  # type: str
        object_definition: ObjectDefinition = utils.first_or_default_where(self.object_definitions,
                                                                           lambda d: d.object_name == object_name)
        return object_definition

    def _query_object(self, database: Database, connection: sqlite3.Connection, object_name: str,
                      id_object: object) -> object:
        object_definition: ObjectDefinition = self.get_object_definition(object_name)
        if object_definition is None:
            raise ValueError(f'Object definition for type {object_name} is not defined')
        name: str
        module: str
        module, name = object_name.split('.')
        object_instance: object = getattr(__import__(module), name)()
        # row = database.query_row(connection, object_definition.table_name, id_object)  # type: DataRow
        column_list: List[str] = [s.src_column for s in object_definition.property_sources if s.type_ in ('property', 'object')]
        ds: DataSet = database.raw_query(connection,
                                         object_definition.table_name,
                                         column_list,
                                         object_definition.object_id + '=' + str(id_object))
        dt: DataTable = ds.tables[object_definition.table_name]
        row: DataRow = list(dt.rows.values())[0]
        for property_source in object_definition.property_sources:
            if property_source.type_ == 'property':
                setattr(object_instance, property_source.name, row.items.get(property_source.src_column))
            elif property_source.type_ == 'object':
                child_object = self._query_object(database, connection, property_source.object_name,
                                                  row.get(property_source.src_column))
                setattr(object_instance, property_source.name, child_object)
            elif property_source.type_ == 'list':
                pass
        return object_instance

    def query_objects(self, database: Database, object_name: str, where_clause: str or None, query_params: Tuple or None) -> List[Any]:
        res = []
        with database.create_connection() as connection:
            res = self._query_objects(database, connection, object_name, where_clause, query_params)
        return res

    def _query_objects(self, database: Database, connection: sqlite3.Connection, object_name: str, where_clause: str,
                       query_params: Tuple) -> List[object]:
        object_definition: ObjectDefinition = self.get_object_definition(object_name)
        if object_definition is None:
            raise ValueError('Object definition for type {t} is not defined'.format(t=object_name))
        name_data = object_name.split('.')
        module = '.'.join(name_data[:-1])
        name = name_data[-1]

        column_list = [s.src_column for s in object_definition.property_sources if s.type_ in ('property', 'object')]
        ds: DataSet = database.raw_query(connection,
                                         object_definition.table_name,
                                         column_list,
                                         where_clause,
                                         query_params)
        dt: DataTable = ds.tables[object_definition.table_name]

        res: List[object] = []
        row: DataRow
        for row in dt.rows.values():
            object_instance = getattr(importlib.import_module(module), name)()
            for property_source in object_definition.property_sources:
                if property_source.type_ == 'property':
                    setattr(object_instance, property_source.name, row.items.get(property_source.src_column))
                elif property_source.type_ == 'object':
                    child_object_id = row.get(property_source.src_column)
                    if child_object_id is not None:
                        child_object_where_clause = property_source.src_column + '=?'
                        child_object = self._query_objects(database,
                                                           connection,
                                                           property_source.object_name,
                                                           child_object_where_clause,
                                                           (row.get(property_source.src_column),))[0]
                        setattr(object_instance, property_source.name, child_object)
                elif property_source.type_ == 'list':
                    child_object_where_clause = property_source.src_column + '=?'
                    child_objects = self._query_objects(database,
                                                        connection,
                                                        property_source.object_name,
                                                        child_object_where_clause,
                                                        (row.get(property_source.src_column),))
                    setattr(object_instance, property_source.name, child_objects)
            res.append(object_instance)
        return res

    def _object_to_dataset(self, database: Database, connection: sqlite3.Connection, obj: object) -> DataSet:
        res: DataSet = DataSet()
        object_name: str = obj.__module__ + '.' + obj.__class__.__name__
        object_definition: ObjectDefinition = self.get_object_definition(object_name)
        if object_definition is None:
            raise ValueError(f'Object definition for type {type(obj)} is not defined')
        res.tables[object_definition.table_name] = DataTable(object_definition.table_name)
        row: DataRow = DataRow(object_definition.table_name, getattr(obj, object_definition.object_id))
        property_source: PropertySource
        for property_source in object_definition.property_sources:
            if property_source.type_ == 'property':
                row.items[property_source.src_column] = getattr(obj, property_source.name)
            elif property_source.type_ == 'object':
                child_obj = getattr(obj, property_source.name)
                if child_obj is not None:
                    child_ds = self._object_to_dataset(database, connection, child_obj)
                    res.merge(child_ds)
                    child_object_definition: ObjectDefinition = self.get_object_definition(
                        child_obj.__module__ + '.' + child_obj.__class__.__name__)
                    row.items[property_source.src_column] = getattr(child_ds, child_object_definition.object_id)
            elif property_source.type_ == 'list':
                pass
        res.merge_row(row)
        return res

    # def query(self, database: Database, object_type: Type, object_id: object) -> object:
    #     res = object_type()
    #
    #     conn = database.create_connection()  # type: sqlite3.Connection
    #     type_name = object_type.__module__ + '.' + object_type.__name__  # type: str
    #
    #     object_definition = utils.first_or_default_where(self.object_definitions, lambda d: d.object_name == type_name)  # type: ObjectDefinition
    #     property_id = utils.first_or_default_where(object_definition.property_sources, lambda s: s.name == object_definition.object_id)  # type: PropertySource
    #     ds = database.query(conn, property_id.src_table, object_id, True)  # type: DataSet
    #     dt = ds.tables[property_id.src_table]
    #     row = list(dt.rows.values())[0]
    #     for property_source in object_definition.property_sources:
    #         if property_source.type_ == 'property':
    #             if property_source.src_table == dt.table_name:
    #                 setattr(res, property_source.name, row.items.get(property_source.src_column))
    #             else:
    #
    #     return res
    #
    # def _query_object(self, connection: sqlite3.Connection, database: Database, object_type: Type, object_id: object) -> object:
    #     res = object_type()
    #     type_name = object_type.__module__ + '.' + object_type.__name__  # type: str
    #     object_definition = utils.first_or_default_where(self.object_definitions, lambda d: d.object_name == type_name)  # type: ObjectDefinition
    #     property_id = utils.first_or_default_where(object_definition.property_sources, lambda s: s.name == object_definition.object_id)  # type: PropertySource
    #     # ds = database.query(connection, property_id.src_table, object_id, True)  # type: DataSet
    #     # dt = ds.tables[property_id.src_table]
    #     # row = list(dt.rows.values())[0]
    #     row = database.query_row(connection, property_id.src_table, object_id)
    #     for property_source in object_definition.property_sources:
    #         if property_source.type_ == 'property':
    #             if property_source.src_table == property_id.src_table:
    #                 setattr(res, property_source.name, row.items.get(property_source.src_column))
    #             else:
    #                 reference_id = row.get(property_source.src_column)
    #                 if reference_id is not None:
    #                     # ds_temp = database.query(connection, property_source.referenced_table, row.get(property_source.src_column), True)
    #                     # dt_temp = ds_temp.tables[property_source.src_table]
    #                     # row_temp = list(dt_temp.rows.values())[0]
    #                     row_temp = database.query_row(connection, property_source.referenced_table, row.get(property_source.src_column))
    #                     setattr(res, property_source.name, row_temp.items.get(property_source.referenced_column))
    #         elif property_source.type_ == 'object':
    #             property_type = type(getattr(res, property_source.name))
    #             obj = self._query_object(connection, database, property_type, )
    #     return res
