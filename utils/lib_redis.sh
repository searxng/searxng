#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later

# shellcheck disable=SC2091
# shellcheck source=utils/lib.sh
. /dev/null

REDIS_USER="searxng-redis"
REDIS_GROUP="searxng-redis"

REDIS_SERVICE_NAME="searxng-redis"
REDIS_SYSTEMD_UNIT="${SYSTEMD_UNITS}/${REDIS_SERVICE_NAME}.service"

redis.help() {
    cat <<EOF
redis.:
  remove    : delete user (${REDIS_USER}) and remove service (${REDIS_SERVICE_NAME})
  userdel   : delete user (${REDIS_USER})
  rmgrp     : remove <user> from group (${REDIS_USER})
EOF
}

redis.remove() {
    sudo_or_exit
    (
        set -e
        redis._remove_service
        redis.userdel
    )
    dump_return $?
}

redis.shell() {
    interactive_shell "${REDIS_USER}"
}

redis.userdel() {
    sudo_or_exit
    drop_service_account "${REDIS_USER}"
    groupdel "${REDIS_GROUP}" 2>&1 | prefix_stdout || true
}

redis.addgrp() {

    # usage: redis.addgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -a "$1" "${REDIS_GROUP}"
}

redis.rmgrp() {

    # usage: redis.rmgrp <user>

    [[ -z $1 ]] && die_caller 42 "missing argument <user>"
    sudo -H gpasswd -d "$1" "${REDIS_GROUP}"

}

redis._remove_service() {
    systemd_remove_service "${REDIS_SERVICE_NAME}" "${REDIS_SYSTEMD_UNIT}"
}
