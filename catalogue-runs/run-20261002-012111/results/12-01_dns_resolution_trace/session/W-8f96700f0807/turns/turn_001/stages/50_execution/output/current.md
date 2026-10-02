import socket
import struct
import random
import sys

# DNS helper functions

def build_query(qname, qtype=1):  # A record
    # Header
    transaction_id = random.randint(0, 65535)
    flags = 0x0100  # standard query
    qdcount = 1
    ancount = nscount = arcount = 0
    header = struct.pack('!HHHHHH', transaction_id, flags, qdcount, ancount, nscount, arcount)
    # Question
    qname_parts = qname.split('.')
    qname_bytes = b''.join(struct.pack('!B', len(part)) + part.encode() for part in qname_parts) + b'\x00'
    qtype_bytes = struct.pack('!H', qtype)
    qclass_bytes = struct.pack('!H', 1)  # IN
    return transaction_id, header + qname_bytes + qtype_bytes + qclass_bytes

def parse_name(message, offset):
    labels = []
    while True:
        length = message[offset]
        if length & 0xC0 == 0xC0:  # pointer
            pointer = ((length & 0x3F) << 8) | message[offset + 1]
            pointed_name, _ = parse_name(message, pointer)
            labels.append(pointed_name)
            offset += 2
            break
        if length == 0:
            offset += 1
            break
        offset += 1
        labels.append(message[offset:offset+length].decode())
        offset += length
    return '.'.join(labels), offset

def parse_response(data, transaction_id):
    if len(data) < 12:
        raise ValueError('Response too short')
    resp_id, flags, qdcount, ancount, nscount, arcount = struct.unpack('!HHHHHH', data[:12])
    if resp_id != transaction_id:
        raise ValueError('Transaction ID mismatch')
    offset = 12
    # skip question section
    for _ in range(qdcount):
        _, offset = parse_name(data, offset)
        offset += 4  # type and class
    records = []
    for count, rtype in [(ancount, 'answer'), (nscount, 'ns'), (arcount, 'ar')]:
        for _ in range(count):
            name, offset = parse_name(data, offset)
            rtype_val, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
            offset += 10
            rdata = data[offset:offset+rdlength]
            offset += rdlength
            record = {'name': name, 'type': rtype_val, 'class': rclass, 'ttl': ttl}
            if rtype_val == 1:  # A
                record['address'] = socket.inet_ntoa(rdata)
            elif rtype_val == 5:  # CNAME
                cname, _ = parse_name(data, offset - rdlength)
                record['cname'] = cname
            elif rtype_val == 2:  # NS
                nsdname, _ = parse_name(data, offset - rdlength)
                record['nsdname'] = nsdname
            records.append(record)
    return records

def send_query(server_ip, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(message, (server_ip, 53))
        data, _ = sock.recvfrom(512)
    finally:
        sock.close()
    return data

def iterative_resolve(domain, root_servers):
    qname = domain
    current_servers = root_servers
    while True:
        transaction_id, query = build_query(qname)
        # Send to first server in the current list
        server_ip = current_servers[0]
        print(f"\nSending query for {qname} to {server_ip} (role: {'root' if server_ip in root_servers else 'intermediate'})")
        response_data = send_query(server_ip, query)
        print(f"Received response from {server_ip} (hex): {response_data.hex()}")
        records = parse_response(response_data, transaction_id)
        # Print records for debugging
        for rec in records:
            print('Record:', rec)
        # Check for CNAME
        cname_records = [r for r in records if r['type'] == 5]
        if cname_records:
            cname = cname_records[0]['cname']
            print(f"CNAME found: {qname} -> {cname}")
            qname = cname
            current_servers = root_servers
            continue
        # Check for answer A records
        a_records = [r for r in records if r['type'] == 1]
        if a_records:
            print('Final A records:')
            for a in a_records:
                print(f"{a['name']} -> {a['address']}")
            break
        # No answer, look for NS records
        ns_records = [r for r in records if r['type'] == 2]
        if not ns_records:
            raise RuntimeError('No NS records and no answer; cannot continue')
        # Resolve NS hostnames to IPs using the same resolver (recursive on the NS name)
        next_ips = []
        for ns in ns_records:
            ns_name = ns['nsdname']
            print(f"Resolving NS {ns_name} to IP using root servers...")
            # Simplified: assume IPv4 address can be obtained via iterative_resolve recursively
            # In a real implementation we would cache/lookup, but for brevity we perform a recursive call.
            try:
                ip = resolve_name_to_ip(ns_name, root_servers)
                next_ips.append(ip)
                print(f"NS {ns_name} resolved to {ip}")
                break  # Prefer first successful
            except Exception as e:
                print(f"Failed to resolve NS {ns_name}: {e}")
        if not next_ips:
            raise RuntimeError('Failed to resolve any NS IPs')
        current_servers = next_ips

def resolve_name_to_ip(name, root_servers):
    # Helper that returns first A record for a name using iterative_resolve logic without printing.
    qname = name
    current_servers = root_servers
    while True:
        transaction_id, query = build_query(qname)
        server_ip = current_servers[0]
        data = send_query(server_ip, query)
        records = parse_response(data, transaction_id)
        cname_records = [r for r in records if r['type'] == 5]
        if cname_records:
            qname = cname_records[0]['cname']
            current_servers = root_servers
            continue
        a_records = [r for r in records if r['type'] == 1]
        if a_records:
            return a_records[0]['address']
        ns_records = [r for r in records if r['type'] == 2]
        if not ns_records:
            raise RuntimeError('No NS records while resolving')
        # pick first NS and resolve its IP recursively
        ns_name = ns_records[0]['nsdname']
        qname = ns_name
        current_servers = root_servers

if __name__ == '__main__':
    # List of root server IPv4 addresses (partial list)
    ROOT_SERVERS = [
        '198.41.0.4',     # a.root-servers.net
        '199.9.14.201',   # b.root-servers.net
        '192.33.4.12',    # c.root-servers.net
        '199.7.91.13',    # d.root-servers.net
        '192.203.230.10',# e.root-servers.net
        '192.5.5.241',    # f.root-servers.net
        '192.112.36.4',   # g.root-servers.net
        '198.97.190.53',  # h.root-servers.net
        '192.36.148.17',  # i.root-servers.net
        '192.58.128.30',  # j.root-servers.net
        '193.0.14.129',   # k.root-servers.net
        '199.7.83.42',    # l.root-servers.net
        '202.12.27.33',   # m.root-servers.net
    ]
    target = 'api.staging.example.com'
    iterative_resolve(target, ROOT_SERVERS)
