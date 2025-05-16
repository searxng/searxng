#!/bin/sh

help() {
    cat <<EOF
Command line:
  -h  Display this help
  -d  Dry run to update the configuration files.
  -f  Always update on the configuration files (existing files are renamed with
      the .old suffix).  Without this option, the new configuration files are
      copied with the .new suffix
Environment variables:
  INSTANCE_NAME settings.yml : general.instance_name
  AUTOCOMPLETE  settings.yml : search.autocomplete
  BASE_URL      settings.yml : server.base_url
  MORTY_URL     settings.yml : result_proxy.url
  MORTY_KEY     settings.yml : result_proxy.key
Volume:
  /etc/searxng  the docker entry point copies settings.yml and uwsgi.ini in
                this directory (see the -f command line option)"
EOF
}

# Parse command line
FORCE_CONF_UPDATE=0
DRY_RUN=0

while getopts "fdh" option
do
    case $option in
        f) FORCE_CONF_UPDATE=1 ;;
        d) DRY_RUN=1 ;;
        h)
            help
            exit 0
            ;;
        *)
            echo "unknow option ${option}"
            exit 42
            ;;
    esac
done

get_searxng_version(){
    su searxng -c \
       'python3 -c "import six; import searx.version; six.print_(searx.version.VERSION_STRING)"' \
       2>/dev/null
}

SEARXNG_VERSION="$(get_searxng_version)"
export SEARXNG_VERSION
echo "SearXNG version ${SEARXNG_VERSION}"

# helpers to update the configuration files
patch_uwsgi_settings() {
    CONF="$1"
    sed -i \
        -e "s|workers = .*|workers = ${UWSGI_WORKERS:-%k}|g" \
        -e "s|threads = .*|threads = ${UWSGI_THREADS:-4}|g" \
        "${CONF}"
}

patch_searxng_settings() {
    CONF="$1"

    export BASE_URL="${BASE_URL%/}/"

    sed -i \
        -e "s|base_url: false|base_url: ${BASE_URL}|g" \
        -e "s/instance_name: \"SearXNG\"/instance_name: \"${INSTANCE_NAME}\"/g" \
        -e "s/autocomplete: \"\"/autocomplete: \"${AUTOCOMPLETE}\"/g" \
        -e "s|ultrasecretkey|$(openssl rand -hex 32)|g" \
        "${CONF}"

    if [ -n "${MORTY_KEY}" ] && [ -n "${MORTY_URL}" ]; then
        sed -i -e "s/image_proxy: false/image_proxy: true/g" "${CONF}"
        {
            echo ""
            echo "# Morty configuration"
            echo "result_proxy:"
            echo "   url: ${MORTY_URL}"
            echo "   key: !!binary \"${MORTY_KEY}\""
        } >> "${CONF}"
    fi

    if [ -n "${PROXY_POOL}" ]; then
        echo "" >> "${CONF}"
        echo "outgoing:" >> "${CONF}"
        echo "  proxies:" >> "${CONF}"
        echo "    all://:" >> "${CONF}"

        IFS=',' set -- $PROXY_POOL
        for proxy in "$@"; do
            echo "      - ${proxy}" >> "${CONF}"
        done
    fi
}

update_conf() {
    FORCE_CONF_UPDATE=$1
    CONF="$2"
    NEW_CONF="${2}.new"
    OLD_CONF="${2}.old"
    REF_CONF="$3"
    PATCH_REF_CONF="$4"

    if [ -f "${CONF}" ]; then
        if [ "${REF_CONF}" -nt "${CONF}" ]; then
            if [ "$FORCE_CONF_UPDATE" -ne 0 ]; then
                printf '⚠️  Automatically update %s to the new version\n' "${CONF}"
                if [ ! -f "${OLD_CONF}" ]; then
                    printf 'The previous configuration is saved to %s\n' "${OLD_CONF}"
                    mv "${CONF}" "${OLD_CONF}"
                fi
                cp "${REF_CONF}" "${CONF}"
                $PATCH_REF_CONF "${CONF}"
            else
                printf '⚠️  Check new version %s to make sure SearXNG is working properly\n' "${NEW_CONF}"
                cp "${REF_CONF}" "${NEW_CONF}"
                $PATCH_REF_CONF "${NEW_CONF}"
            fi
        else
            printf 'Use existing %s\n' "${CONF}"
        fi
    else
        printf 'Create %s\n' "${CONF}"
        cp "${REF_CONF}" "${CONF}"
        $PATCH_REF_CONF "${CONF}"
    fi
}

# searx compatibility
SEARX_CONF=0
if [ -f "/etc/searx/settings.yml" ]; then
    if  [ ! -f "${SEARXNG_SETTINGS_PATH}" ]; then
        printf '⚠️  /etc/searx/settings.yml is copied to /etc/searxng\n'
        cp "/etc/searx/settings.yml" "${SEARXNG_SETTINGS_PATH}"
    fi
    SEARX_CONF=1
fi
if [ -f "/etc/searx/uwsgi.ini" ]; then
    printf '⚠️  /etc/searx/uwsgi.ini is ignored. Use the volume /etc/searxng\n'
    SEARX_CONF=1
fi
if [ "$SEARX_CONF" -eq "1" ]; then
    printf '⚠️  The deprecated volume /etc/searx is mounted. Please update your configuration to use /etc/searxng ⚠️\n'
    cat << EOF > /etc/searx/deprecated_volume_read_me.txt
This Docker image uses the volume /etc/searxng
Update your configuration:
* remove uwsgi.ini (or very carefully update your existing uwsgi.ini using https://github.com/searxng/searxng/blob/master/dockerfiles/uwsgi.ini )
* mount /etc/searxng instead of /etc/searx
EOF
fi

update_conf "${FORCE_CONF_UPDATE}" "${UWSGI_SETTINGS_PATH}" "/usr/local/searxng/dockerfiles/uwsgi.ini" "patch_uwsgi_settings"
update_conf "${FORCE_CONF_UPDATE}" "${SEARXNG_SETTINGS_PATH}" "/usr/local/searxng/searx/settings.yml" "patch_searxng_settings"

if [ $DRY_RUN -eq 1 ]; then
    printf 'Dry run\n'
    exit
fi

unset MORTY_KEY

printf 'Listen on %s\n' "${BIND_ADDRESS}"

exec uwsgi --http-socket "${BIND_ADDRESS}" "${UWSGI_SETTINGS_PATH}"
