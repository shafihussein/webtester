Author: SHAFE AHMED  
Student ID: 0V00977399

# WebTester Usage Guide

## What WebTester Does
WebTester.py is a Python 3 command-line program that reads a single URL from standard input (stdin) and prints analysis results to standard output (stdout). It reports whether the server appears to support HTTP/2, lists cookies set by the server, and notes if the page is password-protected. Keep in mind that this README covers usage only—no implementation details are provided.

## How to Run WebTester.py
WebTester.py does not take command-line arguments. Always provide the URL through stdin; output goes to stdout unless you redirect it.

### 1) Run interactively (manual input)
Start the program, then type or paste a URL and press Enter.
```bash
python3 WebTester.py
```
(then type a URL and press Enter)

### 2) Provide a URL via stdin using echo (pipeline)
Use `echo` to send the URL into stdin.
```bash
echo "https://www.example.com/" | python3 WebTester.py
```

### 3) Provide a URL via stdin using printf (alternative to echo)
`printf` can be more reliable for exact formatting (includes the newline).
```bash
printf "https://www.example.com/\n" | python3 WebTester.py
```

### 4) Provide the URL from a file using input redirection
Ensure the file contains exactly one URL on a single line with no extra text or blank lines.
```bash
python3 WebTester.py < url.txt
```

### 5) Redirect stdout to a file (save output)
Capture the results by redirecting stdout.
```bash
echo "https://www.example.com/" | python3 WebTester.py > output.txt
```

### 6) View output on screen AND save it using tee
`tee` shows the output and saves it at the same time.
```bash
echo "https://www.example.com/" | python3 WebTester.py | tee output.txt
```

### 7) Combine input file and output redirection
Use a URL file for input while saving the results to another file.
```bash
python3 WebTester.py < url.txt > output.txt
```

## Output Description
The program prints a concise report that includes:
- website
- Supports http2
- List of Cookies
- Password-protected

Example (sample format only):
```
website: https://www.example.com/
Supports http2: Yes
List of Cookies: session_id=abc123; tracking=on
Password-protected: No
```
