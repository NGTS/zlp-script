import sqlite3
from ngts_catalogue.metadata import Metadata

Metadata.database_name = '/tmp/metadata.sqlite'

def test_database_construction():
    m = Metadata(None)
    keys = m.SCHEMA_MAP.keys()

    with sqlite3.connect(m.database_name) as connection:
        cursor = connection.cursor()

        cursor.execute('select name from sqlite_master where type = "table"')
        assert cursor.fetchone()[0] == 'metadata'

        cursor.execute('pragma table_info(metadata)')
        for row in cursor:
            assert row[1] in keys

def test_render_data():
    test_data = {'pv2_1': 12.2, 'pv2_3': 12.2, 'pv2_5': 12.1, 'cd1_1': 12.2, 'cd1_2': 12.2, 'cd2_1': 12.2, 'cd2_2': 12.2, 'cmd_ra': 12.2, 'cmd_dec': 12.2, 'tel_ra': 12.2, 'tel_dec': 12.2, 'actionid': 12, 'exposure': 12.2, 'cts_med': 12.2, 'airmass': 12.2, 'skylevel': 12.2, 'ra_offset': 12.2, 'dec_offset': 12.2, 'filename': 'test', }

    m = Metadata([test_data])
    m.render()

    with sqlite3.connect(m.database_name) as connection:
        cursor = connection.cursor()
        cursor.execute('select * from metadata limit 1')

        assert sorted(cursor.fetchone()) == sorted(test_data.values() + [1])



