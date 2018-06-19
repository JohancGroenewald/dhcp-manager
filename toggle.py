#!/usr/bin/env python
# coding=utf-8

"""dhcp.conf gateway toggle"""

from __future__ import print_function
import sys
import argparse
from collections import OrderedDict

from master import OUTFILE, EOL


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-c', '--computer', help="Computer name", type=str
    )
    parser.add_argument(
        '-g', '--gateway', help="Gateway", type=str
    )

    args = parser.parse_args(arguments)

    with open(OUTFILE) as f:
        buffer = f.read()
    if len(buffer) == 0:
        print('{} is empty'.format(OUTFILE))
        return
    lines = buffer.split(EOL)

    def clean(line, exclude):
        return line[:-1].replace(exclude, '').replace(' ', '')

    show = args.computer is None and args.gateway is None
    name = args.computer is not None
    gateway = args.gateway is not None
    host_pattern = 'host '
    gateway_pattern = '  option routers '
    no_gateway_message = '<NoGateway>'

    if show:
        computers = []
        for line in lines:
            computer = line.startswith(host_pattern)
            if computer:
                computers.append(clean(line, host_pattern))
        for computer in computers:
            print(computer)
    elif name:
        named_computer = None
        computer_info = []
        for i, line in enumerate(lines):
            if named_computer is None:
                computer = line.startswith(
                    '{}{}'.format(host_pattern, args.computer)
                )
                if computer:
                    named_computer = line
            else:
                end_brace = line == '}'
                computer_info.append(i)
                if end_brace:
                    break
        if named_computer is None:
            print('Computer Not found')
        else:
            print(named_computer)
            gateway_updated = False
            for i in computer_info:
                print(lines[i])
                info_gateway = lines[i].startswith(gateway_pattern)
                if info_gateway and gateway:
                    lines[i] = '{}{};'.format(gateway_pattern, args.gateway)
                    gateway_updated = True
            if gateway_updated:
                print(named_computer)
                for i in computer_info:
                    print(lines[i])
                with open(OUTFILE, 'w') as f:
                    f.write(EOL.join(lines))
                print('<dhcp.conf successfully updated>')
            else:
                print(no_gateway_message)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
