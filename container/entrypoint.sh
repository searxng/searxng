#!/bin/sh
# shellcheck shell=dash
set -u

# Check if it's a valid file
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

# Check if it's a valid directory
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

    target_ownership=$(stat -c %U:%G "$target")

    if [ "$target_ownership" != "searxng:searxng" ]; then
        if [ "${FORCE_OWNERSHIP:-true}" = true ] && [ "$(id -u)" -eq 0 ]; then
            chown -R searxng:searxng "$target"
        else
            cat <<EOF
!!!
!!! WARNING
!!! "$target" $type is not owned by "searxng:searxng"
!!! This may cause issues when running SearXNG
!!!
!!! Expected "searxng:searxng"
!!! Got "$target_ownership"
!!!
EOF
        fi
    fi
}

# Handle volume mounts
volume_handler() {
    local target="$1"

    check_directory "$target"
    setup_ownership "$target" "directory"
}

setup() {
    local template_settings="/usr/local/searxng/settings.template.yml"
    local target_settings="$__SEARXNG_CONFIG_PATH/settings.yml"

    if [ ! -f "$target_settings" ]; then
        cat <<EOF
...
... INFORMATION
... "$target_settings" does not exist, creating from template...
...
EOF
        cp -pfT "$template_settings" "$target_settings"

        sed -i "s/ultrasecretkey/$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')/g" "$target_settings"
    fi

    check_file "$target_settings"
}

cat <<EOF
SearXNG $__SEARXNG_VERSION
EOF

# Check for volume mounts
volume_handler "$__SEARXNG_CONFIG_PATH"
volume_handler "$__SEARXNG_DATA_PATH"

setup

# root only features
if [ "$(id -u)" -eq 0 ]; then
    update-ca-certificates
fi

# ENVs aliases
export GRANIAN_PORT="${SEARXNG_PORT:-$GRANIAN_PORT}"

exec /usr/local/searxng/.venv/bin/granian searx.webapp:app
