import logging
from functools import partial
import sys

__all__ = ['logger']

format_string = '%(asctime)s|%(levelname)s|%(module)s:%(lineno)d|pid:%(process)d|%(message)s'
logging.basicConfig(level=logging.DEBUG, format=format_string, stream=sys.stdout)

class NGTSLogger(object):
    def __init__(self):
        self.logger = logging.getLogger('ngts_catalogue')
        self.log_level = self.logger.getEffectiveLevel()

        level_map = {
                'debug': logging.DEBUG,
                'info': logging.INFO,
                'warning': logging.WARNING,
                'error': logging.ERROR,
                'critical': logging.CRITICAL
                }

        for level_name, level in level_map.iteritems():
            fn = partial(self.logger.log, level)
            setattr(self, level_name.lower(), fn)

    def enable_debug(self):
        self.logger.setLevel(logging.DEBUG)

    def disable_debug(self):
        self.logger.setLevel(self.log_level)

logger = NGTSLogger()
