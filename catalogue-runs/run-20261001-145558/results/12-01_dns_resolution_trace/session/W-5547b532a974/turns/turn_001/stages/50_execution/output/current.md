import socket
import struct
import random

def build_dns_query(domain, qtype=1):
    # Header: ID, flags, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT
    transaction_id = random.randint(0, 65535)
    flags = 0x0100  # standard query
    qdcount = 1
    header = struct.pack('!HHHHHH', transaction_id, flags, qdcount, 0, 0, 0)
    # Question section
    def encode_name(name):
        parts = name.split('.')
        result = b''
        for part in parts:
            length = len(part)
            result += struct.pack('B', length) + part.encode()
        result += b'\0'
        return result
    question = encode_name(domain) + struct.pack('!HH', qtype, 1)  # QTYPE, QCLASS=IN
    return transaction_id, header + question

def parse_dns_response(data):
    # Very minimal parser to extract answers, authority, and additional sections
    header = struct.unpack('!HHHHHH', data[:12])
    transaction_id, flags, qdcount, ancount, nscount, arcount = header
    offset = 12
    # skip questions
    for _ in range(qdcount):
        while data[offset] != 0:
            offset += data[offset] + 1
        offset += 5  # null byte + QTYPE(2) + QCLASS(2)
    answers = []
    for _ in range(ancount):
        name, offset = decode_name(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        answers.append((rtype, rdata))
    authorities = []
    for _ in range(nscount):
        name, offset = decode_name(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        authorities.append((rtype, rdata))
    additionals = []
    for _ in range(arcount):
        name, offset = decode_name(data, offset)
        rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        additionals.append((rtype, rdata))
    return answers, authorities, additionals

def decode_name(data, offset):
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            offset += 1
            break
        # pointer?
        if (length & 0xC0) == 0xC0:
            pointer = ((length & 0x3F) << 8) | data[offset+1]
            pointed_name, _ = decode_name(data, pointer)
            labels.append(pointed_name)
            offset += 2
            break
        else:
            offset += 1
            labels.append(data[offset:offset+length].decode())
            offset += length
    return '.'.join(labels), offset

def ipv4_from_bytes(rdata):
    return '.'.join(str(b) for b in rdata)

def resolve(domain, qtype=1):
    # Root server list (one example)
    root_servers = ["198.41.0.4"]  # a.root-servers.net
    trace = []
    current_name = domain
    current_qtype = qtype
    ns_ip = root_servers[0]
    while True:
        txid, query = build_dns_query(current_name, current_qtype)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        try:
            sock.sendto(query, (ns_ip, 53))
            data, _ = sock.recvfrom(512)
        finally:
            sock.close()
        trace.append((ns_ip, query, data))
        answers, authorities, additionals = parse_dns_response(data)
        # Check for answer of requested type
        for rtype, rdata in answers:
            if rtype == current_qtype:
                if current_qtype == 1:  # A record
                    return trace, ipv4_from_bytes(rdata)
                elif current_qtype == 28:  # AAAA record
                    return trace, socket.inet_ntop(socket.AF_INET6, rdata)
        # Check for CNAME
        for rtype, rdata in answers:
            if rtype == 5:  # CNAME
                cname, _ = decode_name(rdata + b'\0', 0)
                current_name = cname
                # continue loop with same ns_ip
                break
        else:
            # No CNAME in answers, look for NS referral
            ns_name = None
            for rtype, rdata in authorities:
                if rtype == 2:  # NS record
                    ns_name, _ = decode_name(rdata + b'\0', 0)
                    break
            if ns_name is None:
                raise Exception('No NS record found in authority section')
            # Try to find its IP in additionals
            ns_ip = None
            for rtype, rdata in additionals:
                if rtype == 1:  # A record
                    ip = ipv4_from_bytes(rdata)
                    ns_ip = ip
                    break
            if ns_ip is None:
                # Resolve NS name recursively
                sub_trace, ns_ip = resolve(ns_name, 1)
                trace.extend(sub_trace)
    # unreachable

if __name__ == "__main__":
    domain = "api.staging.example.com"
    trace, ip = resolve(domain, 1)
    for ns_ip, query, response in trace:
        print(f"Query to {ns_ip}:")
        print(query.hex())
        print("Response:")
        print(response.hex())
        print("---")
    print(f"Final resolved IP: {ip}")
