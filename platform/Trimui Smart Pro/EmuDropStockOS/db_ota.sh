#!/bin/sh
# Game catalogue updates, pulled from the upstream project that publishes it.
#
# Only the catalogue. app_ota.sh stays disabled on purpose: this build is
# modified (Vietnamese UI, download and thermal changes) and an upstream app
# release would overwrite all of it.
#
# Upstream tags a catalogue release as <version>-db; every other tag is an app
# release. Hardened against the original's failure mode, where a 404 or a
# half-finished download replaced a working 24MB catalogue with an error page.

cd "$(dirname "$0")" 2>/dev/null || exit 0

REPO="ahmadteeb/EmuDrop"
VERSION_FILE="version.txt"
API_URL="https://api.github.com/repos/$REPO/tags"
DB_PATH="assets/catalog.db"
TMP_DB="assets/catalog.db.new"

notify() {
    if [ -n "$INFOSCREEN" ] && [ -f "$INFOSCREEN" ]; then
        "$INFOSCREEN" -m "$1" -t "${2:-0.2}" 2>/dev/null || true
    fi
    echo "$1"
}

get_local_version() {
    if [ -f "$VERSION_FILE" ] && [ -f "$DB_PATH" ]; then
        sed -n '2p' "$VERSION_FILE" | tr -d '[:space:]'
    else
        echo "v0.0.0"
    fi
}

get_latest_version() {
    # Tolerate any spacing the API happens to use around the colon.
    latest=$(curl -sf -k --max-time 20 "$API_URL" \
        | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' \
        | grep -- '-db' | head -n 1 | cut -d '"' -f 4)
    [ -z "$latest" ] && return 1
    case "$latest" in
        v*) ;;
        *) latest="v$latest" ;;
    esac
    echo "${latest%-db}"
}

# Never hand the app anything that is not a complete SQLite file: an error page
# or a half-served file would leave it with an empty game list.
#
# The header carries the page size (bytes 16-17) and the page count (bytes
# 28-31), both big-endian. Their product must equal the file size, which is a
# far tighter check than "large enough and starts with the magic string" - a
# file cut in half passes that one.
valid_db() {
    [ -f "$1" ] || return 1

    size=$(wc -c < "$1" 2>/dev/null | tr -d '[:space:]')
    [ -n "$size" ] || return 1
    [ "$size" -gt 1048576 ] || return 1
    head -c 15 "$1" 2>/dev/null | grep -q "SQLite format 3" || return 1

    page_hex=$(od -An -tx1 -j16 -N2 "$1" 2>/dev/null | tr -d ' \n')
    count_hex=$(od -An -tx1 -j28 -N4 "$1" 2>/dev/null | tr -d ' \n')
    if [ ${#page_hex} -ne 4 ] || [ ${#count_hex} -ne 8 ]; then
        echo "Note: could not read the SQLite header with od, size check only."
        return 0
    fi

    page_size=$((0x$page_hex))
    page_count=$((0x$count_hex))
    # A stored page size of 1 means 65536.
    [ "$page_size" -eq 1 ] && page_size=65536
    [ "$page_size" -gt 0 ] && [ "$page_count" -gt 0 ] || return 1

    expected=$((page_size * page_count))
    if [ "$expected" -ne "$size" ]; then
        echo "Incomplete database: $size bytes, header describes $expected."
        return 1
    fi
    return 0
}

keep_local() {
    rm -f "$TMP_DB"
    echo "$1 Keeping the catalogue already installed."
    notify "Database update skipped" 0.2
    exit 0
}

echo "Checking for update for database..."

local_version=$(get_local_version)
latest_version=$(get_latest_version) || keep_local "Could not reach GitHub, or no -db release was listed."

echo "Local version: $local_version"
echo "Latest version: $latest_version"

if [ "$local_version" = "$latest_version" ]; then
    echo "You are already on the latest version: $latest_version"
    exit 0
fi

echo "New update available: $latest_version"
notify "Updating game database..." 0.2

url="https://github.com/$REPO/releases/download/$latest_version-db/catalog-$latest_version.db"
echo "Downloading from: $url"
mkdir -p assets
rm -f "$TMP_DB"

# -f turns an HTTP error into a failure instead of a saved error page.
if ! curl -fL -k --max-time 900 --retry 2 -o "$TMP_DB" "$url"; then
    keep_local "Download failed."
fi

if ! valid_db "$TMP_DB"; then
    keep_local "The downloaded file is not a usable SQLite database."
fi

# Swap in one move, so there is no window where the app has no catalogue.
if ! mv -f "$TMP_DB" "$DB_PATH"; then
    keep_local "Could not replace the catalogue file."
fi

# Line 1 is the app version, line 2 the catalogue version. Rewritten in full
# rather than with sed -i, whose -i flag takes an argument on some platforms.
app_line=$(head -n 1 "$VERSION_FILE" 2>/dev/null)
printf '%s\n%s\n' "$app_line" "$latest_version" > "$VERSION_FILE.tmp" \
    && mv -f "$VERSION_FILE.tmp" "$VERSION_FILE"

echo "Database update complete: $latest_version"
notify "Game database updated" 0.2
exit 0
