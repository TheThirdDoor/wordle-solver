#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 filename"
    exit 1
fi

file="$1"

# 1. Print the 2-line header
head -n 2 "$file"

# 2. Find the line number of the FIRST blank line followed by an equals sign
# We subtract 1 to get the last line of the sortable data
end_line=$(grep -n -m 1 "^$" "$file" | cut -d: -f1)

# 3. Extract the sortable block (Lines 3 to end_line-1)
# Then sort it by the text after the colon
sed -n "3,$((end_line - 1))p" "$file" | sort -t ':' -k 2

# 4. Print everything from the blank line to the end of the file
tail -n +"$end_line" "$file"