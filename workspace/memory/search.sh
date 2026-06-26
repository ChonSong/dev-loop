#!/bin/bash
# Memory Search Utility
# Search through curated memory entries by tag, keyword, or date

set -e

# Paths
WORKSPACE="/home/osboxes/.openclaw/workspace"
MAIN_MEMORY="$WORKSPACE/MEMORY.md"
MEMORY_DIR="$WORKSPACE/zoul/memory"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_usage() {
    cat << EOF
Memory Search Utility

Usage: $0 [OPTIONS] [SEARCH_TERM]

Options:
  -t, --tag TAG        Search by tag (#preference, #project, #decision, #lesson)
  -k, --keyword KEY   Search by keyword
  -d, --date DATE     Search by date (YYYY-MM-DD or YYYY-MM for range)
  -r, --recent N       Show N most recent entries (default: 10)
  -a, --all           Search in all memory files, not just main MEMORY.md
  -h, --help          Show this help message

Examples:
  $0 -t decision                    # Search for all decisions
  $0 -k agent                       # Search for entries with 'agent'
  $0 -d 2026-03                    # Search for entries from March 2026
  $0 -r 20                         # Show 20 most recent entries
  $0 -t lesson -k automation        # Search for automation lessons

Tags:
  #preference  - User preferences and settings
  #project     - Project milestones and progress
  #decision    - Architectural and technical decisions
  #lesson      - Lessons learned and patterns

EOF
}

# Supported tags
SUPPORTED_TAGS=("preference" "project" "decision" "lesson")

# Parse arguments
TAG=""
KEYWORD=""
DATE=""
RECENT=10
SEARCH_ALL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -k|--keyword)
            KEYWORD="$2"
            shift 2
            ;;
        -d|--date)
            DATE="$2"
            shift 2
            ;;
        -r|--recent)
            RECENT="$2"
            shift 2
            ;;
        -a|--all)
            SEARCH_ALL=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            if [ -z "$KEYWORD" ]; then
                KEYWORD="$1"
            else
                echo -e "${RED}Error: Multiple search terms provided${NC}"
                print_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate tag if provided
if [ -n "$TAG" ]; then
    valid_tag=false
    for supported_tag in "${SUPPORTED_TAGS[@]}"; do
        if [ "$TAG" == "$supported_tag" ]; then
            valid_tag=true
            break
        fi
    done

    if [ "$valid_tag" = false ]; then
        echo -e "${RED}Error: Invalid tag '$TAG'${NC}"
        echo "Valid tags: ${SUPPORTED_TAGS[*]}"
        exit 1
    fi
fi

# Function to search in main memory
search_main_memory() {
    local pattern="$1"
    local filter_tag="$2"
    local filter_date="$3"
    local limit="$4"

    if [ ! -f "$MAIN_MEMORY" ]; then
        echo -e "${RED}Error: Main memory file not found: $MAIN_MEMORY${NC}"
        return 1
    fi

    local results=0
    local search_cmd="grep"

    # Build search pattern
    if [ -n "$filter_tag" ]; then
        search_cmd="$search_cmd '#$filter_tag'"
    elif [ -n "$filter_date" ]; then
        if [[ "$filter_date" =~ ^[0-9]{4}-[0-9]{2}$ ]]; then
            # Monthly range
            search_cmd="$search_cmd '$filter_date'"
        else
            # Exact date
            search_cmd="$search_cmd '^$filter_date'"
        fi
    elif [ -n "$pattern" ]; then
        search_cmd="$search_cmd -i '$pattern'"
    else
        # Default: show all tagged entries
        search_cmd="$search_cmd -E '#(preference|project|decision|lesson)'"
    fi

    # Apply filters
    local temp_results=$(mktemp)
    eval "$search_cmd '$MAIN_MEMORY' 2>/dev/null | grep '^-' > '$temp_results'" || true

    # Additional filtering
    local final_results=$(mktemp)
    local need_and=false

    # Filter by tag if specified
    if [ -n "$filter_tag" ]; then
        if [ -n "$pattern" ]; then
            grep "#$filter_tag" "$temp_results" | grep -i "$pattern" > "$final_results"
        else
            grep "#$filter_tag" "$temp_results" > "$final_results"
        fi
    elif [ -n "$filter_date" ]; then
        if [ -n "$pattern" ]; then
            grep "$filter_date" "$temp_results" | grep -i "$pattern" > "$final_results"
        else
            grep "$filter_date" "$temp_results" > "$final_results"
        fi
    elif [ -n "$pattern" ]; then
        grep -i "$pattern" "$temp_results" > "$final_results"
    else
        cp "$temp_results" "$final_results"
    fi

    # Count results
    results=$(wc -l < "$final_results" 2>/dev/null || echo "0")

    # Display results
    if [ "$results" -gt 0 ]; then
        echo -e "${GREEN}Found $results result(s):${NC}"
        echo ""

        # Apply limit
        if [ -n "$limit" ] && [ "$results" -gt "$limit" ]; then
            head -n "$limit" "$final_results"
            echo ""
            echo -e "${CYAN}... ($((results - limit)) more results not shown)${NC}"
        else
            cat "$final_results"
        fi
    else
        echo -e "${YELLOW}No results found${NC}"
    fi

    # Cleanup
    rm -f "$temp_results" "$final_results"

    return 0
}

# Function to search in all memory files
search_all_memory() {
    local pattern="$1"
    local filter_tag="$2"
    local filter_date="$3"

    if [ ! -d "$MEMORY_DIR" ]; then
        echo -e "${RED}Error: Memory directory not found: $MEMORY_DIR${NC}"
        return 1
    fi

    local total_results=0

    echo -e "${BLUE}Searching in all memory files...${NC}"
    echo ""

    for file in $(find "$MEMORY_DIR" -name "*.md" -type f 2>/dev/null | sort -r); do
        local file_name=$(basename "$file")

        echo -e "${CYAN}--- $file_name ---${NC}"

        local search_cmd="grep"

        # Build search pattern
        if [ -n "$filter_tag" ]; then
            search_cmd="$search_cmd '#$filter_tag'"
        elif [ -n "$filter_date" ]; then
            search_cmd="$search_cmd '$filter_date'"
        elif [ -n "$pattern" ]; then
            search_cmd="$search_cmd -i '$pattern'"
        else
            search_cmd="$search_cmd -E '#(preference|project|decision|lesson)'"
        fi

        eval "$search_cmd '$file' 2>/dev/null" || true
        echo ""
    done
}

# Main search logic
echo -e "${BLUE}Memory Search${NC}"
echo "========================================"

if [ "$SEARCH_ALL" = true ]; then
    search_all_memory "$KEYWORD" "$TAG" "$DATE"
else
    search_main_memory "$KEYWORD" "$TAG" "$DATE" "$RECENT"
fi

echo ""
echo "========================================"
