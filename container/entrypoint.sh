#!/bin/sh
# shellcheck shell=dash
set -u

check_file() {
    local target="$1"

    if [ ! -f "$target" ]; then
        cat <<EOF
!!!
!!! ERROR
!!! "$target" is not a valid file, exiting...
!!!
EOF
        exit 127
    fi
}

check_directory() {
    local target="$1"

    if [ ! -d "$target" ]; then
        cat <<EOF
!!!
!!! ERROR
!!! "$target" is not a valid directory, exiting...
!!!
EOF
        exit 127
    fi
}

setup_ownership() {
    local target="$1"
    local type="$2"

    case "$type" in
    file | directory) ;;
    *)
        cat <<EOF
!!!
!!! ERROR
!!! "$type" is not a valid type, exiting...
!!!
EOF
        exit 1
        ;;
    esac

    if [ "$(stat -c %U:%G "$target")" != "searxng:searxng" ]; then
        if [ "$(id -u)" -eq 0 ]; then
            chown -R searxng:searxng "$target"
        else
            cat <<EOF
!!!
!!! WARNING
!!! "$target" $type is not owned by "searxng"
!!! This may cause issues when running SearXNG
!!!
!!! Run the container as root to fix this issue automatically
!!! Alternatively, you can chown the $type manually:
!!! $ chown -R searxng:searxng "$target"
!!!
EOF
        fi
    fi
}

# Apply envs to uwsgi.ini
setup_uwsgi() {
    local timestamp

    timestamp=$(stat -c %Y "$UWSGI_SETTINGS_PATH")

    sed -i \
        -e "s|workers = .*|workers = ${UWSGI_WORKERS:-%k}|g" \
        -e "s|threads = .*|threads = ${UWSGI_THREADS:-4}|g" \
        "$UWSGI_SETTINGS_PATH"

    # Restore timestamp
    touch -c -d "@$timestamp" "$UWSGI_SETTINGS_PATH"
}

# Apply envs to settings.yml
setup_searxng() {
    local timestamp

    timestamp=$(stat -c %Y "$SEARXNG_SETTINGS_PATH")

    # Ensure trailing slash in BASE_URL
    # https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Shell-Parameter-Expansion
    export BASE_URL="${BASE_URL%/}/"

    sed -i \
        -e "s|base_url: false|base_url: ${BASE_URL:-false}|g" \
        -e "s/instance_name: \"SearXNG\"/instance_name: \"${INSTANCE_NAME:-SearXNG}\"/g" \
        -e "s/autocomplete: \"\"/autocomplete: \"${AUTOCOMPLETE:-}\"/g" \
        -e "s/ultrasecretkey/$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')/g" \
        "$SEARXNG_SETTINGS_PATH"

    # Restore timestamp
    touch -c -d "@$timestamp" "$SEARXNG_SETTINGS_PATH"
}

# Handle volume mounts
volume_handler() {
    local target="$1"

    # Check if it's a valid directory
    check_directory "$target"
    setup_ownership "$target" "directory"
}

# Handle configuration file updates
config_handler() {
    local target="$1"
    local template="$2"
    local new_template_target="$target.new"

    # Create/Update the configuration file
    if [ -f "$target" ]; then
        setup_ownership "$target" "file"

        if [ "$template" -nt "$target" ]; then
            cp -pfT "$template" "$new_template_target"

            cat <<EOF
...
... INFORMATION
... Update available for "$target"
... It is recommended to update the configuration file to ensure proper functionality
...
... New version placed at "$new_template_target"
... Please review and merge changes
...
EOF
        fi
    else
        cat <<EOF
...
... INFORMATION
... "$target" does not exist, creating from template...
...
EOF
        cp -pfT "$template" "$target"
    fi

    # Check if it's a valid file
    check_file "$target"
}

echo "SearXNG $SEARXNG_VERSION"

# Check for volume mounts
volume_handler "$CONFIG_PATH"
volume_handler "$DATA_PATH"

# Check for updates in files
config_handler "$UWSGI_SETTINGS_PATH" "/usr/local/searxng/.template/uwsgi.ini"
config_handler "$SEARXNG_SETTINGS_PATH" "/usr/local/searxng/searx/settings.yml"

# Update files
setup_uwsgi
setup_searxng

exec /usr/local/searxng/venv/bin/uwsgi --http-socket "$BIND_ADDRESS" "$UWSGI_SETTINGS_PATH"
