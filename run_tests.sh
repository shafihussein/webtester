#!/bin/bash

# Ensure output directory exists
mkdir -p tests/output

# Loop through all input files
for input_file in tests/input/*; do
    # Skip if no files match
    [ -f "$input_file" ] || continue

    # Extract base filename (e.g., url_01_uvic.txt)
    base_name=$(basename "$input_file")

    # Build output filename (e.g., url_01_uvic_output.txt)
    output_file="tests/output/${base_name%.txt}_output.txt"

    echo "Running WebTester on $base_name"

    # Run WebTester with input redirected from file
    python3 WebTester.py < "$input_file" > "$output_file"
done

echo "All tests completed."
