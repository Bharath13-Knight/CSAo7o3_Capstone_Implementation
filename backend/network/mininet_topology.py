"""
Mininet Multi-Subnet Network Topology with QoS Controls
======================================================
This standalone script builds the complete 3-subnet network architecture
in Mininet for Linux demonstration and hardware-level tc QoS testing.

Subnet A (192.168.1.0/24): PC1 (192.168.1.10), PC2 (192.168.1.20) via Switch s1
Subnet B (192.168.2.0/24): PC3 (192.168.2.10), PC4 (192.168.2.20) via Switch s2
Subnet C (192.168.3.0/24): PC5 (192.168.3.10), PC6 (192.168.3.20) via Switch s3
Router (r1): IP Forwarding enabled with gateway interfaces on all 3 subnets.

Usage on Linux / Mininet:
    sudo python3 mininet_topology.py
"""

import sys

try:
    from mininet.net import Mininet
    from mininet.node import Node, OVSSwitch
    from mininet.cli import CLI
    from mininet.log import setLogLevel, info
    from mininet.link import TCLink
    MININET_AVAILABLE = True
except ImportError:
    MININET_AVAILABLE = False

class LinuxRouter(Node):
    """A Node with IP forwarding enabled to act as a multi-subnet IP Router."""
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

def run_multi_subnet_network():
    if not MININET_AVAILABLE:
        print("[!] Mininet is not installed in this environment.")
        print("    This script is designed for Linux systems with Mininet installed.")
        print("    The web application includes a high-fidelity built-in simulator that")
        print("    emulates this exact multi-subnet routing and QoS environment.")
        return

    setLogLevel('info')
    info('*** Creating Multi-Subnet Mininet Network Topology\n')
    net = Mininet(topo=None, build=False, ipBase='10.0.0.0/8', link=TCLink)

    info('*** Adding Core IP Router\n')
    r1 = net.addHost('r1', cls=LinuxRouter, ip='192.168.1.1/24')

    info('*** Adding Subnet Switches\n')
    s1 = net.addSwitch('s1')  # Subnet A Switch
    s2 = net.addSwitch('s2')  # Subnet B Switch
    s3 = net.addSwitch('s3')  # Subnet C Switch

    info('*** Adding End Hosts for Subnet A, B, and C\n')
    # Subnet A: 192.168.1.0/24
    pc1 = net.addHost('pc1', ip='192.168.1.10/24', defaultRoute='via 192.168.1.1')
    pc2 = net.addHost('pc2', ip='192.168.1.20/24', defaultRoute='via 192.168.1.1')

    # Subnet B: 192.168.2.0/24
    pc3 = net.addHost('pc3', ip='192.168.2.10/24', defaultRoute='via 192.168.2.1')
    pc4 = net.addHost('pc4', ip='192.168.2.20/24', defaultRoute='via 192.168.2.1')

    # Subnet C: 192.168.3.0/24
    pc5 = net.addHost('pc5', ip='192.168.3.10/24', defaultRoute='via 192.168.3.1')
    pc6 = net.addHost('pc6', ip='192.168.3.20/24', defaultRoute='via 192.168.3.1')

    info('*** Creating Links and Gateway Interfaces\n')
    # Connect Router to Switches
    net.addLink(s1, r1, intfName2='r1-eth1', params2={'ip': '192.168.1.1/24'}, bw=100)
    net.addLink(s2, r1, intfName2='r1-eth2', params2={'ip': '192.168.2.1/24'}, bw=100)
    net.addLink(s3, r1, intfName2='r1-eth3', params2={'ip': '192.168.3.1/24'}, bw=100)

    # Connect Hosts to their respective Switches
    net.addLink(pc1, s1, bw=100)
    net.addLink(pc2, s1, bw=100)

    net.addLink(pc3, s2, bw=100)
    net.addLink(pc4, s2, bw=100)

    net.addLink(pc5, s3, bw=100)
    net.addLink(pc6, s3, bw=100)

    info('*** Starting Network\n')
    net.build()
    s1.start([])
    s2.start([])
    s3.start([])

    info('*** Configuring IP Routing on Router Interfaces\n')
    r1.cmd('ip addr add 192.168.2.1/24 dev r1-eth2')
    r1.cmd('ip addr add 192.168.3.1/24 dev r1-eth3')

    info('*** Testing Basic Connectivity (pc1 -> pc3)\n')
    print(pc1.cmd('ping -c 2 192.168.2.10'))

    info('*** Network is ready! Type exit to stop.\n')
    CLI(net)

    info('*** Stopping Network\n')
    net.stop()

if __name__ == '__main__':
    run_multi_subnet_network()
