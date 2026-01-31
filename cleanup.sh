#!/bin/bash

# cleanup.sh - Remove all contents from the output/ directory

OUTPUT_DIR="$(dirname "$0")/tests/output"

# Check if output directory exists
if [ -d "$OUTPUT_DIR" ]; then
    # Remove all files and directories in output/
    rm -rf "$OUTPUT_DIR"/*
    echo "Cleaned up all contents in $OUTPUT_DIR"
else
    echo "Output directory does not exist: $OUTPUT_DIR"
    exit 1
fi
