# coding=utf-8

import datetime

# noinspection PyCompatibility
from ConfigParser import RawConfigParser as ConfParser

VERSION = '201712-0.62d'
HOST_NO_ROUTE = '''{}host {} {{
{}  hardware ethernet {};
{}  fixed-address {}{};
{}  option routers 0.0.0.0;
{}}}'''
HOST_ROUTE = '''{}host {} {{
{}  hardware ethernet {};
{}  fixed-address {}{};
{}  option routers {};
{}}}'''
SUBNET='subnet {} netmask {} {{ range {} {}; }}'
OPTION_ROUTERS = 'option routers {}'
INFILE = 'dhcpd.master'
OUTFILE = 'dhcpd.conf'
HOSTS_FILE = 'hosts.txt'
EOL = '\n'


class Master(object):
    SECTIONS = {
        'required': ['configuration', 'routers', 'gateways', 'subnets'],
        'optional': ['defaults']
    }

    def __init__(self):
        self.configuration = {}
        self.routers = {}
        self.gateways = []
        self.subnets = {}
        self.defaults = {}
        self.networks = []

    def __str__(self):
        buffer = []
        # buffer.append(str(self.configuration))
        # buffer.append(str(self.routers))
        # buffer.append(str(self.gateways))
        # buffer.append(str(self.subnets))
        # buffer.append(str(self.defaults))
        buffer.append(str(self.networks))
        return EOL.join(buffer)

    def load_configuration(self, options):
        for key, value in options:
            self.configuration[key] = value

    def load_routers(self, options):
        for key, value in options:
            self.routers[key] = value

    def load_gateways(self, options):
        for key, value in options:
            self.gateways.append(key)

    def load_subnets(self, options):
        for key, value in options:
            values = self.string2list(value)
            address = values[0][:values[0].rfind('.')+1]
            range = self.string2list(values[2], ':')
            self.subnets[key] = {
                'subnet': values[0],
                'netmask': values[1],
                'range': [address+range[0], address+range[1]]
            }

    def load_defaults(self, options):
        for key, value in options:
            values = self.string2list(value)
            self.defaults[key] = values

    def validate_gateway(self, gateway):
        if gateway and gateway in self.gateways:
            return self.routers[gateway]
        for router, address in self.routers.items():
            if gateway == address:
                if router in self.gateways:
                    return gateway
                else:
                    m = 'Not a valid gateway. [{}]'.format(gateway)
                break
        else:
            m = 'Gateway not available. [{}]'.format(gateway)
        raise ValueError(m)

    def default_gateway(self, gateway):
        if 'gateway' in self.defaults:
            if not gateway:
                router = self.defaults['gateway'][0]
            else:
                router = gateway
            if router in self.routers:
                gateway = self.routers[router]
                return gateway
            else:
                m = 'Default Gateway not in routers. [{}]'
                raise ValueError(m.format(gateway))
        elif not gateway:
            raise ValueError('Default Gateway not available')
        return self.validate_gateway(gateway)

    @staticmethod
    def string2list(string, delimiter=','):
        values = []
        string = string.replace(' ', '')
        if string:
            values = string.split(delimiter)
        return values

    def from_file(self, infile):
        config = ConfParser(allow_no_value=True)
        config.read(infile)
        sections = config.sections()
        required = list(self.SECTIONS['required'])
        for section in sections:
            if section in required:
                required.remove(section)
        if required:
            m = 'Required section(s) not found. {}'
            raise ValueError(m.format(required))
        for required in self.SECTIONS['required']:
            method_name = 'load_' + required
            method = getattr(self, method_name, None)
            if method:
                method(config.items(required))
                config.remove_section(required)
            else:
                m = 'Required class method not found. "{}()"'
                raise AttributeError(m.format(method_name))
        for gateway in self.gateways:
            if gateway not in self.routers:
                m = 'Gateway not in routers. [{}]'.format(gateway)
                raise ValueError(m)
        for optional in self.SECTIONS['optional']:
            method_name = 'load_' + optional
            method = getattr(self, method_name, None)
            if method:
                method(config.items(optional))
            config.remove_section(optional)
        sections = config.sections()
        for section in sections:
            network = {section: []}
            for i, item in enumerate(config.items(section)):
                option, value = item
                values = self.string2list(value)
                network[section].append({option: values})
            self.networks.append(network)

    def to_file(self, outfile, gateway, force_gateway):
        gateway = self.default_gateway(gateway)
        host_buffer = []
        buffer = []
        def add(strings, terminate='', write_buffer=buffer):
            if type(strings) is list:
                message = ''.join(strings)
            else:
                message = strings
            if terminate:
                message += ';'
            write_buffer.append(message)
        spacer = ''
        t = ';'
        add('#'+'-'*79)
        add('# HUIS *dhcpd.conf* auto-generator')
        add(['# Version: ', VERSION])
        add(['# Source: ', INFILE])
        add([
            '# Auto generated on: ',
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        ])
        add('#'+'-'*79)
        add(spacer)
        heading = '# Global Configuration'
        add('{:-<80}'.format(heading))
        keys = self.configuration.keys()
        keys.sort()
        for key in keys:
            value = self.configuration[key]
            if value is None:
                add(key, t)
            else:
                add([key, ' ', value], t)
        add(spacer)
        heading = '# Default gateway'
        if force_gateway:
            heading += ' [Forced]'
        add('{:-<80}'.format(heading))
        add(OPTION_ROUTERS.format(gateway), t)
        add(spacer)
        add('{:-<80}'.format('# Available Routers'))
        sorted_routers = [
            '{} {}{}'.format(
                item[1],
                item[0],
                ' ( Gateway )' if item[0] in self.gateways else ''
            ) for item in self.routers.items()
        ]
        sorted_routers.sort()
        for router in sorted_routers:
            add(['# ', router])
        for router, address in self.routers.items():
            add([address, ' ', router], write_buffer=host_buffer)
        add(spacer)
        for subnet, options in self.subnets.items():
            heading = '# Subnet for {}'.format(subnet)
            add('{:-<80}'.format(heading))
            add(SUBNET.format(
                options['subnet'], options['netmask'],
                options['range'][0], options['range'][1]
            ))
        for network in self.networks:
            name = network.keys()[0]
            options = network[name]
            add(spacer)
            heading = '# {}'.format(name)
            add('{:-<80}'.format(heading))
            default_router = gateway
            network_id = None
            host_id = None
            for option in options:
                key = option.keys()[0]
                if key == 'base_address':
                    network_id = option[key][0]
                    host_id = int(
                        network_id[network_id.rfind('.')+1:]
                    )
                    network_id = network_id[:network_id.rfind('.')+1]
                    continue
                if key == 'default_router' and not force_gateway:
                    default_router = self.validate_gateway(option[key][0])
                    continue
            if network_id is None or host_id is None:
                m = 'Base address not available for the *{}* network'
                raise ValueError(m.format(name.upper()))
            if host_id is None or type(host_id) is not int:
                m = 'Start address not available for the *{}* network'
                raise ValueError(m.format(name.upper()))
            for option in options:
                key = option.keys()[0]
                if key in ['base_address', 'default_router']:
                    continue
                remarked = '# | ' if 'count_only' in option[key] else ''
                if 'no_route' in option[key]:
                    add(HOST_NO_ROUTE.format(
                        remarked, key,
                        remarked, option[key][0],
                        remarked, network_id, host_id,
                        remarked,
                        remarked
                    ))
                else:
                    if 'default_gateway' in option[key]:
                        host_default_router = gateway
                    else:
                        host_default_router = default_router
                    add(HOST_ROUTE.format(
                        remarked, key,
                        remarked, option[key][0],
                        remarked, network_id, host_id,
                        remarked, host_default_router,
                        remarked
                    ))
                strings = [network_id, str(host_id), ' ', key]
                add(strings, write_buffer=host_buffer)
                host_id += 1
        add(spacer)
        add('#'+'-'*79)
        add('# End Of File')
        add('#'+'-'*79)
        with open(outfile, 'w') as f:
            f.write(EOL.join(buffer))
        with open(HOSTS_FILE, 'w') as f:
            f.write(EOL.join(host_buffer))
