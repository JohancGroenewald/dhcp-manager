#!/usr/bin/env python
# coding=utf-8

"""dhcp.conf manager"""

from __future__ import print_function
import sys
import argparse

from master import INFILE, OUTFILE, Master


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-i', '--infile', help="Input file", type=str
    )
    parser.add_argument(
        '-o', '--outfile', help="Output file", type=str
    )
    parser.add_argument(
        '-g', '--gateway', help="Gateway", type=str
    )
    parser.add_argument(
        '-f', '--force-gateway', help="Force gateway", action="store_true"
    )

    args = parser.parse_args(arguments)
    infile = INFILE if args.infile is None else args.infile
    outfile = OUTFILE if args.outfile is None else args.outfile

    master = Master()
    master.from_file(infile)
    master.to_file(
        outfile, args.gateway, args.force_gateway
    )


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
