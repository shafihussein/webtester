WebTester
=========

Overview
--------
WebTester is a Python 3 command-line web client that operates directly on raw sockets and TLS. It highlights low-level protocol handling for HTTP/1.1, HTTPS handshakes, ALPN-based HTTP/2 capability probing (detection only), redirect logic, cookie extraction, authentication checks, and Unix-style stdin/stdout pipelines. The goal is to showcase protocol fluency for recruiters, students, and engineers in a portfolio-friendly project.

Repository Structure
--------------------
```
.
├── WebTester.py        # Core CLI client implemented with sockets + ssl
├── run_tests.sh        # Batch runner that feeds each test input to WebTester
├── tests
│   ├── input           # One URL per file; user-authored test cases
│   │   ├── url_01.txt
│   │   ├── url_02.txt
│   │   └── ...
│   └── output          # Auto-generated stdout captures per test
│       ├── url_01_output.txt
│       ├── url_02_output.txt
│       └── ...
```
- `tests/output` is produced automatically by the test runner and is git-ignored.
- Output files are simply stdout redirected to disk; the code never writes elsewhere.

Features
--------
- Reads a single URL from **stdin** (no command-line arguments).
- Manually parses scheme, host, port, and path.
- Resolves DNS for IPv4 and IPv6.
- Opens TCP sockets directly (no `requests` or `urllib`).
- Performs TLS handshakes for HTTPS.
- Detects HTTP/2 support via ALPN (probe only; data sent over HTTP/1.1).
- Builds and sends raw HTTP/1.1 GET requests.
- Follows 301/302 redirects with loop detection.
- Extracts cookies from `Set-Cookie` headers.
- Flags password-protected pages (HTTP 401).
- Prints a structured, human-readable report to stdout.

How WebTester Works (High Level)
--------------------------------
1. Read the URL from stdin.
2. Parse scheme, host, port, and path manually.
3. Resolve DNS records (IPv4 + IPv6).
4. For HTTPS, perform a TLS handshake and probe ALPN for HTTP/2 support.
5. Open a separate HTTP/1.1 connection for the request.
6. Send the HTTP/1.1 GET and receive the full response.
7. Follow redirects (301/302) until a final response or loop.
8. Parse headers and extract cookies.
9. Print a formatted report to stdout summarizing protocol insights.

Running WebTester
-----------------
WebTester only reads from stdin and only writes to stdout unless redirected. Choose any of these patterns:

1) Interactive input  
```bash
python3 WebTester.py
# then type or paste a URL and press Enter
```

2) Direct URL via echo  
```bash
echo "https://www.example.com/" | python3 WebTester.py
```

3) Direct URL via printf  
```bash
printf "https://www.example.com/\n" | python3 WebTester.py
```

4) URL from a file (input redirection)  
```bash
python3 WebTester.py < tests/input/url_01.txt
```

5) Redirect stdout to a file  
```bash
echo "https://www.example.com/" | python3 WebTester.py > output.txt
```

6) View and save simultaneously (tee)  
```bash
echo "https://www.example.com/" | python3 WebTester.py | tee output.txt
```

Adding and Running Tests
------------------------
- Place all test inputs in `tests/input/`.
- Name each file `url_XX.txt` (two-digit numbering).
- Each file must contain **exactly one line** with a single valid URL.
- No comments, blank lines, or extra text.

**Correct**
```
tests/input/url_23.txt
https://news.ycombinator.com/
```

**Incorrect**
```
tests/input/url_23.txt
https://news.ycombinator.com/
# extra comment    <- not allowed
```
```
tests/input/url_23.txt
https://example.com/
https://example.org/   <- multiple lines not allowed
```

Run the full test suite:
```bash
./run_tests.sh
```
- The script runs WebTester once per `url_XX.txt`.
- Stdin comes from each input file; stdout is redirected to `tests/output/url_XX_output.txt`.
- `tests/output` is created automatically; every input has a one-to-one output file.
- New tests require no code changes—just drop a new `url_XX.txt` and rerun the script.

Output Format (Example)
-----------------------
```
website: www.example.com
1. Supports http2: yes
2. List of Cookies:
cookie name: sessionid, expires time: Tue, 18 Feb 2025 10:00:00 GMT, domain name: .example.com
3. Password-protected: no
--- Additional info ---
scheme: https
final port: 443
resolved ip addresses: 93.184.216.34
final uri: https://www.example.com/
final status code: 200
redirects followed: 1
```

Code Snippets
-------------
Focused excerpts from `WebTester.py`:

**Reading from stdin**
```python
uri = sys.stdin.readline().strip()
if not uri:
    print("Error: No URI provided on stdin", file=sys.stderr)
    sys.exit(1)
```

**Building an HTTP/1.1 request**
```python
request = "GET " + path + " HTTP/1.1\\r\\n"
request += "Host: " + host_header + "\\r\\n"
request += "Connection: close\\r\\n"
request += "User-Agent: WebTester/1.0\\r\\n"
request += "Accept: */*\\r\\n"
request += "\\r\\n"
```

**Detecting HTTP/2 support via ALPN**
```python
context = ssl.create_default_context()
context.set_alpn_protocols(["h2", "http/1.1"])
ssock = context.wrap_socket(raw_sock, server_hostname=host)
ssock.connect(sockaddr)
selected = ssock.selected_alpn_protocol()
supports_h2 = selected == "h2"
```

**Extracting cookies from headers**
```python
set_cookie_values = get_header_values(headers, "Set-Cookie")
for header_value in set_cookie_values:
    parts = header_value.split(";")
    if parts and "=" in parts[0]:
        name = parts[0].split("=", 1)[0].strip()
        cookies.append({"name": name})
```

Design Choices
--------------
- **Raw sockets instead of requests/urllib:** keeps every network step visible—DNS resolution, TCP connect, TLS negotiation, and header parsing.
- **HTTP/2 detection only:** ALPN probing demonstrates server capability while the client stays intentionally focused on HTTP/1.1 semantics.
- **Stdout/stdin pipelines:** Unix-friendly composability; easy redirection, scripting, and CI integration without extra flags.

Limitations
-----------
- No full HTTP/2 implementation (probe only).
- No JavaScript execution or DOM processing.
- Behavior depends on live sites, which may change between runs.

Closing
-------
WebTester is a networking learning project that demonstrates protocol-level understanding of HTTP over raw sockets and TLS. It provides a solid, inspectable foundation for future extensions such as fuller HTTP/2 handling, additional HTTP methods, or deeper cookie and authentication workflows.
