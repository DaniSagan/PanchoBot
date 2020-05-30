from typing import List

from db.database import DataRow, DbSerializable
from db.database import DataSet

TABLE_PARENT = 'table_parent'
TABLE_CHILD = 'table_child'


class ChildObject(DbSerializable):
    def __init__(self):
        self.id_table_child = 0  # type: int
        self.value_1 = ''  # type: str

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['DbSerializable']:
        pass

    def to_data_set(self) -> DataSet:
        ds = DataSet()
        row = DataRow(TABLE_CHILD, self.id_table_child)
        row.put('id_table_child', self.id_table_child)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        return ds


class ParentObject(DbSerializable):
    def __init__(self):
        self.id_table_parent = 0  # type: int
        self.value_1 = ''  # type: str
        self.children = []  # type: List[ChildObject]
        self.single_child = None  # type: ChildObject

    def to_data_set(self) -> DataSet:
        ds = DataSet()
        row = DataRow(TABLE_PARENT, self.id_table_parent)
        row.put('id_table_parent', self.id_table_parent)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        for child in self.children:
            child_ds = child.to_data_set()  # type: DataSet
            child_ds.add_column_to_table(TABLE_CHILD, 'id_table_parent', self.id_table_parent)
            ds.merge(child_ds)
        return ds

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['ParentObject']:
        res = []  # type: List[ParentObject]
        table = data_set.tables[TABLE_PARENT]
        for row_key in table.rows:  # type: DataRow
            obj = ParentObject()
            obj.id_table_parent = table.rows[row_key].get('id_table_parent')
            obj.value_1 = table.rows[row_key].get('value_1')
            res.append(obj)
        return res
