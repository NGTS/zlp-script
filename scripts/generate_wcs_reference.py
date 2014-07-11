#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import
import subprocess as sp
import argparse
import fitsio
import numpy as np
import datetime

class QueryResults(object):
    def __init__(self, results_str):
        self.results_str = results_str

    def extract_lines(self):
        for line in self.results_str.split('\n'):
            if line and '#' not in line:
                yield self.extract_line(line)

    def extract_line(self, line):
        return {'ra': self.extract_ra(line),
                'dec': self.extract_dec(line),
                'jmag': self.extract_jmag(line),
                }

    def extract_ra(self, line):
        return self.__extract_value(line, 0, 10)

    def extract_dec(self, line):
        return self.__extract_value(line, 11, 21)

    def extract_jmag(self, line):
        return self.__extract_value(line, 54, 60)

    @staticmethod
    def __extract_value(line, a, b):
        return float(line[a:b])

    def render_fits(self, outfile, bright, faint):
        data = self.extract_lines()
        data = [row for row in data
                if row['jmag'] <= faint
                and row['jmag'] >= bright]

        keys = data[0].keys()
        out = {key: np.array([row[key] for row in data])
               for key in keys}

        header_info = [
            {'name': 'ftime', 'value': str(datetime.datetime.now()), 'comment': 'Fetch time'}
             ]

        outfile.write(out, header=header_info)

def main(args):
    box_width = 3.              # Box width in degrees
    cmd = map(str, ['find2mass', args.ra, args.dec, '-bd', box_width, '-m', args.nobj,
                    '-lmJ', '{},{}'.format(args.bright, args.faint)])
    results = QueryResults(sp.check_output(cmd))

    with fitsio.FITS(args.output, 'rw', clobber=True) as outfile:
        results.render_fits(outfile, bright=args.bright, faint=args.faint)

if __name__ == '__main__':
    description = '''
    Extract a zlp-compatible reference catalogue from arbitrary sky positions
    '''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-r', '--ra', required=True, type=float, help='Central RA')
    parser.add_argument('-d', '--dec', required=True, type=float, help='Central DEC')
    parser.add_argument('-o', '--output', required=True, help='Output file name')
    parser.add_argument('--faint', required=False, type=float, help='Faint magnitude [default: 14]',
                        default=14)
    parser.add_argument('--bright', required=False, type=float, help='Bright magnitude [default: 8]',
                        default=8)
    parser.add_argument('-n', '--nobj', required=False, default=1E6, type=int,
                        help='Maximum number of objects to retrieve [default: 1E6]')
    main(parser.parse_args())
