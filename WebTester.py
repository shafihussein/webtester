#!/usr/bin/env python3
# shabang line, used when run as executable script

import socket
import ssl
import sys


def parse_uri(uri):
    uri = uri.strip()
    if not uri:
        raise ValueError("Empty URI")

    scheme = "https"
    rest = uri
    scheme_marker = "://"
    marker_index = uri.find(scheme_marker)
    if marker_index != -1:
        scheme = uri[:marker_index].lower()
        rest = uri[marker_index + len(scheme_marker) :]
    if scheme not in ("http", "https"):
        raise ValueError("Unsupported scheme")

    slash_index = rest.find("/")
    if slash_index == -1:
        host_port = rest
        path = "/"
    else:
        host_port = rest[:slash_index]
        path = rest[slash_index:]
        if not path:
            path = "/"

    if not host_port:
        raise ValueError("Missing host")

    host = host_port
    port = 443 if scheme == "https" else 80

    if host_port.startswith("["):
        end_bracket = host_port.find("]")
        if end_bracket == -1:
            raise ValueError("Invalid IPv6 host")
        host = host_port[1:end_bracket]
        remainder = host_port[end_bracket + 1 :]
        if remainder.startswith(":"):
            port_part = remainder[1:]
            if not port_part.isdigit():
                raise ValueError("Invalid port number")
            port = int(port_part)
    elif ":" in host_port:
        host_part, port_part = host_port.rsplit(":", 1)
        if not port_part.isdigit():
            raise ValueError("Invalid port number")
        host = host_part
        port = int(port_part)

    if not path.startswith("/"):
        path = "/" + path

    return scheme, host, port, path


def default_port_for_scheme(scheme):
    return 443 if scheme == "https" else 80


def host_for_uri(host):
    if ":" in host and not host.startswith("["):
        return "[" + host + "]"
    return host


def build_request(host, port, path, scheme):
    host_header = host
    default_port = default_port_for_scheme(scheme)
    if ":" in host and not host.startswith("["):
        host_header = "[" + host + "]"
    if port != default_port:
        host_header = host_header + ":" + str(port)

    request = "GET " + path + " HTTP/1.1\r\n"
    request += "Host: " + host_header + "\r\n"
    request += "Connection: close\r\n"
    request += "User-Agent: WebTester/1.0\r\n"
    request += "Accept: */*\r\n"
    request += "\r\n"
    return request


def resolve_host_ips(host, port):
    ips = []
    try:
        info_list = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise RuntimeError("DNS lookup failed: " + str(e))

    for info in info_list:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


def open_connection(scheme, host, port):
    last_error = None
    try:
        addr_list = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise RuntimeError("DNS lookup failed: " + str(e))

    for family, socktype, proto, cname, sockaddr in addr_list:
        raw_sock = socket.socket(family, socktype, proto)
        raw_sock.settimeout(10)
        try:
            if scheme == "https":
                context = ssl.create_default_context()
                context.set_alpn_protocols(["http/1.1"])
                ssock = context.wrap_socket(raw_sock, server_hostname=host)
                ssock.settimeout(10)
                ssock.connect(sockaddr)
                return ssock, None
            raw_sock.connect(sockaddr)
            return raw_sock, None
        except Exception as e:
            last_error = e
            try:
                raw_sock.close()
            except Exception:
                pass
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Connection failed")


def send_http_request(sock, request):
    try:
        data = request.encode("ascii", "ignore")
    except Exception:
        data = request.encode()
    sock.sendall(data)


def receive_response(sock):
    chunks = []
    while True:
        try:
            part = sock.recv(4096)
        except socket.timeout:
            break
        if not part:
            break
        chunks.append(part)
    return b"".join(chunks)


def split_headers_body(response_bytes):
    marker = b"\r\n\r\n"
    idx = response_bytes.find(marker)
    if idx == -1:
        return response_bytes, b""
    return response_bytes[:idx], response_bytes[idx + len(marker) :]


def parse_status_code(header_bytes):
    lines = header_bytes.split(b"\r\n")
    if not lines:
        return 0
    try:
        first = lines[0].decode("iso-8859-1", "ignore")
    except Exception:
        return 0
    parts = first.split()
    if len(parts) < 2:
        return 0
    try:
        return int(parts[1])
    except Exception:
        return 0


def get_header_values(header_bytes, header_name):
    values = []
    lines = header_bytes.split(b"\r\n")
    target = header_name.lower()
    for line in lines:
        try:
            text = line.decode("iso-8859-1", "ignore")
        except Exception:
            continue
        if ":" not in text:
            continue
        name, value = text.split(":", 1)
        if name.strip().lower() == target:
            values.append(value.strip())
    return values


def extract_cookies(header_bytes):
    cookies = []
    set_cookie_values = get_header_values(header_bytes, "Set-Cookie")
    for header_value in set_cookie_values:
        parts = header_value.split(";")
        if not parts:
            continue
        first = parts[0].strip()
        if "=" not in first:
            continue
        name = first.split("=", 1)[0].strip()
        if not name:
            continue
        cookie = {"name": name}
        for attr in parts[1:]:
            attr = attr.strip()
            if "=" not in attr:
                continue
            attr_name, attr_val = attr.split("=", 1)
            attr_name = attr_name.strip().lower()
            attr_val = attr_val.strip()
            if attr_name == "expires":
                cookie["expires"] = attr_val
            elif attr_name == "domain":
                cookie["domain"] = attr_val
        cookies.append(cookie)
    return cookies


def check_password_protection(status_code):
    return "yes" if status_code == 401 else "no"


def detect_http2_support(host, port):
    last_error = None
    try:
        addr_list = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise RuntimeError("DNS lookup failed: " + str(e))

    for family, socktype, proto, cname, sockaddr in addr_list:
        raw_sock = socket.socket(family, socktype, proto)
        raw_sock.settimeout(10)
        try:
            context = ssl.create_default_context()
            context.set_alpn_protocols(["h2", "http/1.1"])
            ssock = context.wrap_socket(raw_sock, server_hostname=host)
            ssock.settimeout(10)
            ssock.connect(sockaddr)
            selected = ssock.selected_alpn_protocol()
            ssock.close()
            if selected == "h2":
                return True
            return False
        except Exception as e:
            last_error = e
            try:
                raw_sock.close()
            except Exception:
                pass
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Connection failed")


def resolve_redirect_uri(current_uri, location_value):
    scheme, host, port, _ = parse_uri(current_uri)
    default_port = default_port_for_scheme(scheme)
    port_part = "" if port == default_port else ":" + str(port)
    host_part = host_for_uri(host)

    if location_value.startswith("http://") or location_value.startswith("https://"):
        return location_value.strip()
    if location_value.startswith("/"):
        return scheme + "://" + host_part + port_part + location_value
    if not location_value.startswith("/"):
        location_value = "/" + location_value
    return scheme + "://" + host_part + port_part + location_value


def follow_redirects(initial_uri):
    visited = set()
    current = initial_uri
    supports_h2 = False
    redirects = 0

    while True:
        if current in visited:
            raise RuntimeError("Redirect loop detected")
        visited.add(current)

        scheme, host, port, path = parse_uri(current)
        if scheme == "https":
            try:
                if detect_http2_support(host, port):
                    supports_h2 = True
            except Exception:
                # If probing fails, continue to attempt normal request to report error later if needed
                pass

        request = build_request(host, port, path, scheme)
        sock, alpn = open_connection(scheme, host, port)
        send_http_request(sock, request)
        response = receive_response(sock)
        sock.close()

        headers, _ = split_headers_body(response)
        status = parse_status_code(headers)

        if status in (301, 302):
            locations = get_header_values(headers, "Location")
            if not locations:
                return {
                    "final_uri": current,
                    "headers": headers,
                    "status": status,
                    "supports_h2": supports_h2,
                    "redirects": redirects,
                }
            next_uri = resolve_redirect_uri(current, locations[0])
            current = next_uri
            redirects += 1
            continue

        return {
            "final_uri": current,
            "headers": headers,
            "status": status,
            "supports_h2": supports_h2,
            "redirects": redirects,
        }


def format_cookies_output(cookies):
    if not cookies:
        return "(none)"
    lines = []
    for cookie in cookies:
        line = "cookie name: " + cookie["name"]
        if "expires" in cookie:
            line += ", expires time: " + cookie["expires"]
        if "domain" in cookie:
            line += ", domain name: " + cookie["domain"]
        lines.append(line)
    return "\n".join(lines)


def print_report(
    host,
    http2_support,
    cookies,
    password_protected,
    scheme,
    port,
    ip_list,
    final_uri,
    status_code,
    redirect_count,
):
    print("website: " + host)
    print("1. Supports http2: " + http2_support)
    print("2. List of Cookies:")
    print(format_cookies_output(cookies))
    print("3. Password-protected: " + password_protected)
    print("--- Additional info ---")
    print("scheme: " + scheme)
    print("final port: " + str(port))
    if ip_list:
        print("resolved ip addresses: " + ", ".join(ip_list))
    else:
        print("resolved ip addresses: (none)")
    print("final uri: " + final_uri)
    print("final status code: " + str(status_code))
    print("redirects followed: " + str(redirect_count))


# main
def main():
    try:
        uri = sys.stdin.readline().strip()
        if not uri:
            print("Error: No URI provided on stdin", file=sys.stderr)
            sys.exit(1)

        redirect_result = follow_redirects(uri)
        final_uri = redirect_result["final_uri"]
        headers = redirect_result["headers"]
        status_code = redirect_result["status"]
        http2_support = "yes" if redirect_result["supports_h2"] else "no"
        redirect_count = redirect_result["redirects"]

        scheme, host, port, _ = parse_uri(final_uri)
        ip_list = resolve_host_ips(host, port)
        cookies = extract_cookies(headers)
        password_protected = check_password_protection(status_code)

        print_report(
            host,
            http2_support,
            cookies,
            password_protected,
            scheme,
            port,
            ip_list,
            final_uri,
            status_code,
            redirect_count,
        )

    except ValueError as e:
        print("Error: Invalid URI format: " + str(e), file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print("Error: " + str(e), file=sys.stderr)
        sys.exit(1)
    except ssl.SSLError as e:
        print("Error: SSL failure: " + str(e), file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print("Error: Connection timeout", file=sys.stderr)
        sys.exit(1)
    except socket.error as e:
        print("Error: Network connection failed: " + str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("Error: Unexpected error: " + str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
