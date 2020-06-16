from typing import List

from db.database import DataRow, DbSerializable, DataSet
from db.database import DataSet

TABLE_PARENT = 'table_parent'
TABLE_CHILD = 'table_child'


class ChildObject(DbSerializable):
    def __init__(self):
        self.id_table_child: int = 0
        self.value_1: str = ''

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
        self.id_table_parent: int = 0
        self.value_1: str = ''
        self.children: List[ChildObject] = []
        self.single_child: ChildObject = None

    def to_data_set(self) -> DataSet:
        ds: DataSet = DataSet()
        row: DataRow = DataRow(TABLE_PARENT, self.id_table_parent)
        row.put('id_table_parent', self.id_table_parent)
        row.put('value_1', self.value_1)
        ds.merge_row(row)
        child: ChildObject
        for child in self.children:
            child_ds: DataSet = child.to_data_set()
            child_ds.add_column_to_table(TABLE_CHILD, 'id_table_parent', self.id_table_parent)
            ds.merge(child_ds)
        return ds

    @classmethod
    def from_data_set(cls, data_set: DataSet) -> List['ParentObject']:
        res: List[ParentObject] = []
        table = data_set.tables[TABLE_PARENT]
        row_key: DataRow
        for row_key in table.rows:
            obj: ParentObject = ParentObject()
            obj.id_table_parent = table.rows[row_key].get('id_table_parent')
            obj.value_1 = table.rows[row_key].get('value_1')
            res.append(obj)
        return res
