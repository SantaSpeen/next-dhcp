import ipaddress
import platform
import random
import re
import subprocess
from dataclasses import dataclass, field

from dhcppython import options
from loguru import logger

from core.exceptions import InvalidDHCPConfiguration


def get_range(network):
    """Get the first and last host in a network"""
    first_host = network.network_address + 1
    last_host = network.broadcast_address - 1
    return int(first_host), int(last_host)


def get_all_interfaces():
    os_type = platform.system()
    try:
        if os_type == "Windows":
            return get_windows_ips()
        elif os_type == "Linux":
            return get_linux_ips()
        else:
            raise NotImplementedError(f"OS '{os_type}' not supported")
    except Exception as e:
        logger.exception(e)

def get_windows_ips():
    ips = []
    command = "powershell -Command \"& {chcp 437; ipconfig}\""
    output = subprocess.check_output(command, shell=True)
    output = output.decode('cp437', errors='ignore')
    lines = output.splitlines()
    for line in lines:
        ip_match = re.search(r'IPv4 Address[. ]+:\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line)
        if ip_match:
            ips.append(ip_match.group(1))
    return ips

def get_linux_ips():
    ips = []
    output = subprocess.check_output(["ip", "addr"], encoding='latin1')
    lines = output.splitlines()
    for line in lines:
        if "inet " in line:
            ip_match = re.search(r'inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line)
            if ip_match:
                ips.append(ip_match.group(1))
    return ips

@dataclass
class DHCPServerConfiguration:
    """Class for storing the configuration of the DHCP server"""
    network: ipaddress.IPv4Network = ipaddress.ip_network('10.15.0.0/24')
    range: tuple[int, int] = field(default_factory=lambda: (170852353, 170852606))  # 10.47.0.1, 10.47.0.254
    router: str = field(default_factory=lambda: '10.15.0.1')
    domain: str = field(default_factory=lambda: 'local')
    lease_time: int = 300
    domain_name_servers: set = field(default_factory=lambda: {"1.1.1.1", "8.8.8.8", "9.9.9.9"})
    server_ip: ipaddress.IPv4Address = field(default_factory=lambda: None)

    @property
    def dhcp_range_len(self):
        return self.range[1] - self.range[0]

    def check(self):
        """Check if the configuration is valid"""
        if self.server_ip is None:
            raise InvalidDHCPConfiguration(f"No valid IPs on any interface (maybe not in DHCP network?)\n{get_all_interfaces()}")
        logger.success(f"Using interface with '{self.server_ip}' for DHCP Server.")
        s, e = ipaddress.IPv4Address(self.range[0]), ipaddress.IPv4Address(self.range[1])
        if s not in self.network or e not in self.network:
            raise InvalidDHCPConfiguration(f"Bad DHCP range: '{s}'-'{e}' not in network")
        if self.dhcp_range_len < 2:
            raise InvalidDHCPConfiguration(f"Bad DHCP range: range is too small")
        if ipaddress.IPv4Address(self.router) not in self.network:
            logger.warning("Router not in network")

    def in_range(self, ip):
        """Check if an IP address is in the DHCP range"""
        return ipaddress.ip_address(ip) in self.network

    def random_ip(self):
        """Return a random IP address in the DHCP range"""
        return str(ipaddress.ip_address(random.randint(*self.range)))

    def as_dict(self):
        return {
            "network": str(self.network),
            "range": [str(ipaddress.ip_address(self.range[0])), str(ipaddress.ip_address(self.range[1]))],
            "router": str(self.router),
            "domain": self.domain,
            "lease_time": self.lease_time,
            "domain_name_servers": list(self.domain_name_servers),
            "server_ip": str(self.server_ip),
        }

    @classmethod
    def from_dict(cls, data):
        """Create a configuration object from a dictionary"""
        data['network'] = ipaddress.ip_network(data['network'])
        if data.get('dhcp_range'):
            s, e = ipaddress.IPv4Address(data['dhcp_range'][0]), ipaddress.IPv4Address(data['dhcp_range'][1])
            data['dhcp_range'] = (int(s), int(e))
        else:
            data['dhcp_range'] = get_range(data['network'])
        return cls(**data)

    @property
    def options(self):
        """Return the options for the configuration"""
        return options.OptionList(
            [
                # Netmask
                options.options.short_value_to_object(1, str(self.network.netmask)),
                # Router(s)
                options.options.short_value_to_object(3, [str(self.router)]),
                # DNS
                options.options.short_value_to_object(6, self.domain_name_servers),
                # Domain name (also known as search domain)
                options.options.short_value_to_object(15, self.domain),
                # Broadcast address
                options.options.short_value_to_object(28, self.network.broadcast_address),
                # Address lease time
                options.options.short_value_to_object(51, self.lease_time),
                # DHCP server identifier
                options.options.short_value_to_object(54, self.server_ip),
                # Renewal time value #1
                options.options.short_value_to_object(58, int(self.lease_time*0.5)),
                # Renewal time value #2
                options.options.short_value_to_object(59, int(self.lease_time*0.875)),
            ]
        )

