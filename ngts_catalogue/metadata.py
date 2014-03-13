import sqlite3
import copy

__all__ = ['render_metadata']

class Metadata(object):
    SCHEMA_MAP = {
            'id': 'integer primary key',
            'pv2_1': 'float',
            'pv2_3': 'float',
            'pv2_5': 'float',
            'cd1_1': 'float',
            'cd1_2': 'float',
            'cd2_1': 'float',
            'cd2_2': 'float',
            'cmd_ra': 'float',
            'cmd_dec': 'float',
            'tel_ra': 'float',
            'tel_dec': 'float',
            'actionid': 'integer',
            'exposure': 'float',
            'cts_med': 'float',
            'airmass': 'float',
            'skylevel': 'float',
            'ra_offset': 'float',
            'dec_offset': 'float',
            'filename': 'string',
            }

    database_name = 'metadata.sqlite'

    def __init__(self, extracted_metadata):
        self.data = extracted_metadata
        self.database_name = 'metadata.sqlite'
        self.create_database()

    def create_database(self):
        with sqlite3.connect(self.database_name) as connection:
            cursor = connection.cursor()
            schema = self.build_schema()
            try:
                cursor.execute('drop table metadata')
            except sqlite3.OperationalError:
                pass
            finally:
                cursor.execute(schema)

    def build_schema(self):
        column_descriptions = ','.join(['{} {}'.format(key, value)
            for (key, value) in self.SCHEMA_MAP.iteritems()])
        return 'create table metadata ({})'.format(column_descriptions)

    def render(self):
        columns = copy.copy(self.SCHEMA_MAP)
        del columns['id']
        keys = columns.keys()
        placeholders = [':{}'.format(key) for key in keys]

        with sqlite3.connect(self.database_name) as connection:
            query = '''insert into metadata ({}) values ({})'''.format(','.join(keys),
                    ','.join(placeholders))
            cursor = connection.cursor()
            cursor.executemany(query,
                self.data)

        return self
