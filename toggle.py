#!/usr/bin/env python
# coding=utf-8

"""dhcp.conf gateway toggle"""

from __future__ import print_function
import sys
import argparse

from master import OUTFILE, EOL

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-c', '--client', help="Client name", type=str
    )
    parser.add_argument(
        '-g', '--gateway', help="Gateway", type=str
    )

    args = parser.parse_args(arguments)
    show = args.client is None and args.gateway is None

    host_mask = 'host '
    gateway_mask = 'option routers '

    with open(OUTFILE) as f:
        buffer = f.read()
    lines = buffer.split(EOL)
    state = 0
    m = ''

    def clean(line, exclude):
        return line[:-1].replace(exclude, '').replace(' ', '')

    for line in lines:
        h = line.startswith(host_mask)
        o = line.find(gateway_mask)
        if h and state == 0:
            m = clean(line, host_mask)
            state = 1
        elif h and state == 1:
            print('NoGateway {}'.format(m))
            m = clean(line, host_mask)
            state = 0
        elif o >= 0 and state == 1:
            print('{} {}'.format(
                clean(line, gateway_mask), m
            ))
            state = 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
