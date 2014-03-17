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

    @staticmethod
    def extract_image_data(filename):
        keys = ['PV2_1', 'PV2_3', 'PV2_5', 'CMD_RA', 'CMD_DEC',
                'TEL_RA', 'TEL_DEC', 'ACTIONID', 'EXPOSURE', 'CTS_MED', 'AIRMASS',
                'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2', 'SKYLEVEL']

        with fitsio.FITS(filename) as infile:
            header = infile[0].read_header()
            header_items = {key.lower(): header[key] for key in keys}

        meta_items = {'filename': os.path.basename(filename)}

        return dict(header_items.items() + meta_items.items())

    @staticmethod
    def extract_catalogue_data(filename):
        with fitsio.FITS(filename) as infile:
            return { 'nobj': infile[1].read_header()['naxis2'] }

    @staticmethod
    def extract_computed_data(image_name, catalogue, extra_metadata):
        '''
        Extract important header keywords and statistics of the solution

        Inputs:

        - the solved image name
        - the catalogue used to solve the image
        - extra metadata to store
        '''
        image_data = Metadata.extract_image_data(image_name)
        catalogue_data = Metadata.extract_catalogue_data(catalogue)

        payload = dict(image_data.items() + catalogue_data.items() + extra_metadata.items())
        return { 'status': 'ok', 'data': payload }
