import json
from .ngts_logging import logger
import copy
import fitsio
import os

__all__ = ['Metadata']

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
            'extra': 'string',
            }

    filename = 'metadata.json'

    def __init__(self, extracted_metadata):
        self.data = extracted_metadata

    def render(self):
        logger.info('Rendering metadata to file {0}'.format(self.filename))
        with open(self.filename, 'w') as outfile:
            json.dump(self.data, outfile)

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

    @classmethod
    def extract_computed_data(cls, image_name, catalogue, extra_metadata={}):
        '''
        Extract important header keywords and statistics of the solution

        Inputs:

        - the solved image name
        - the catalogue used to solve the image
        - extra metadata to store
        '''
        image_data = cls.extract_image_data(image_name)
        catalogue_data = cls.extract_catalogue_data(catalogue)
        success = {'success': True}

        items = dict(image_data.items() +
                catalogue_data.items() +
                extra_metadata.items() +
                success.items())
        return items

    @classmethod
    def extract_failure_data(cls, exc, image_name, catalogue):
        usual_items = cls.extract_computed_data(image_name, catalogue)
        error_data = {'error_message': str(exc), 'success': False}
        items = dict(usual_items.items() + error_data.items())
        return items
