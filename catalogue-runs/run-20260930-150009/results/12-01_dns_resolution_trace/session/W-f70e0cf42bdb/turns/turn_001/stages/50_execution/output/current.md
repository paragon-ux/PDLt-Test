# resolver.py
"""Simplified iterative DNS resolver using UDP sockets.

It traces the DNS resolution path for a given domain starting from an empty cache,
showing each query sent to the root, TLD, and authoritative name servers, and
handling CNAME records by restarting the lookup for the canonical name.

Usage example (run the script):
    python resolver.py api.staging.example.com
"""
import socket
import struct
import random
import sys

# Root server IPv4 addresses (a subset for brevity)
ROOT_SERVERS = [
    "198.41.0.4",   # a.root-servers.net
    "199.9.14.201", # b.root-servers.net
    "192.33.4.12",  # c.root-servers.net
]

def build_query(domain, qtype=1):  # qtype 1 = A
    transaction_id = random.randint(0, 0xFFFF)
    flags = 0x0100  # standard query
    qdcount = 1
    ancount = nscount = arcount = 0
    header = struct.pack('!HHHHHH', transaction_id, flags, qdcount, ancount, nscount, arcount)
    # encode domain name
    qname = b''.join(bytes([len(part)]) + part.encode() for part in domain.split('.')) + b'\0'
    question = qname + struct.pack('!HH', qtype, 1)  # QTYPE, QCLASS=1 (IN)
    return transaction_id, header + question

def parse_name(message, offset):
    labels = []
    while True:
        length = message[offset]
        if length == 0:
            offset += 1
            break
        # pointer?
        if (length & 0xC0) == 0xC0:
            pointer = ((length & 0x3F) << 8) | message[offset+1]
            pointed_name, _ = parse_name(message, pointer)
            labels.append(pointed_name)
            offset += 2
            break
        else:
            offset += 1
            labels.append(message[offset:offset+length].decode())
            offset += length
    return '.'.join(labels), offset

def parse_response(data, query_id):
    transaction_id, flags, qdcount, ancount, nscount, arcount = struct.unpack('!HHHHHH', data[:12])
    if transaction_id != query_id:
        raise ValueError('Transaction ID mismatch')
    offset = 12
    # skip question section
    for _ in range(qdcount):
        _, offset = parse_name(data, offset)
        offset += 4  # QTYPE + QCLASS
    answers = []
    authorities = []
    additionals = []
    def read_rr():
        nonlocal offset
        name, offset = parse_name(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        return {
            'name': name,
            'type': rtype,
            'class': rclass,
            'ttl': ttl,
            'rdata': rdata,
        }
    for _ in range(ancount):
        answers.append(read_rr())
    for _ in range(nscount):
        authorities.append(read_rr())
    for _ in range(arcount):
        additionals.append(read_rr())
    return answers, authorities, additionals

def rdata_to_ip(rdata):
    return '.'.join(str(b) for b in rdata)

def rdata_to_name(rdata, message):
    # rdata contains a pointer or name; reuse parse_name
    offset = len(message) - len(rdata)
    name, _ = parse_name(message, offset)
    return name

def udp_query(server, query):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.sendto(query, (server, 53))
        data, _ = sock.recvfrom(512)
    finally:
        sock.close()
    return data

def resolve(domain):
    log = []
    target = domain
    while True:
        # start at roots
        servers = ROOT_SERVERS
        while True:
            qid, query = build_query(target)
            server = servers[0]
            log.append(f"Query {target} to {server}")
            response = udp_query(server, query)
            answers, auth, addl = parse_response(response, qid)
            # check for answer
            if answers:
                for ans in answers:
                    if ans['type'] == 5:  # CNAME
                        cname = rdata_to_name(ans['rdata'], response)
                        log.append(f"CNAME {target} -> {cname}")
                        target = cname
                        # restart from root for canonical name
                        servers = ROOT_SERVERS
                        break
                    elif ans['type'] == 1:  # A
                        ip = rdata_to_ip(ans['rdata'])
                        log.append(f"Answer A {target} = {ip}")
                        return ip, log
                else:
                    # no relevant answer, continue processing authorities
                    pass
            # handle delegation
            ns_names = []
            for ns in auth:
                if ns['type'] == 2:  # NS
                    ns_name = rdata_to_name(ns['rdata'], response)
                    ns_names.append(ns_name)
            if not ns_names:
                raise RuntimeError('No NS records in authority section')
            # Resolve NS names using additionals or separate queries (simplified: use first NS IP from additionals)
            ns_ips = []
            for add in addl:
                if add['type'] == 1:  # A
                    ip = rdata_to_ip(add['rdata'])
                    ns_ips.append(ip)
            if not ns_ips:
                # fallback: query first NS name directly (recursive call with recursion disabled)
                ns_ip, _ = resolve(ns_names[0])
                ns_ips.append(ns_ip)
            servers = ns_ips
            # loop to next level
    
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python resolver.py <domain>')
        sys.exit(1)
    domain = sys.argv[1]
    ip, steps = resolve(domain)
    print('Resolution steps:')
    for s in steps:
        print(' -', s)
    print(f'Final IP for {domain}: {ip}')
