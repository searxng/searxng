#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

valkey.distro.setup() {
    # shellcheck disable=SC2034

    case $DIST_ID in
        ubuntu | debian)
            VALKEY_PACKAGES="valkey-server"
            ;;
        arch | fedora | centos)
            VALKEY_PACKAGES="valkey"
            ;;
        *)
            err_msg "$DIST_ID: valkey not yet implemented"
            ;;
    esac
}

valkey.backports() {

    case $DIST_ID in
        debian)
            info_msg "APT:: install debian-stable-backports.source / ${DIST_ID}-${DIST_VERS} (${DIST_VERSION_CODENAME})"
            install_template /etc/apt/sources.list.d/debian-stable-backports.sources
            apt update
            ;;
        ubuntu)
            info_msg "APT:: install ubuntu-stable-backports.source / ${DIST_ID}-${DIST_VERS} (${DIST_VERSION_CODENAME})"
            install_template /etc/apt/sources.list.d/ubuntu-stable-backports.sources
            apt update
            ;;
        *)
            info_msg "APT:: valkey.backports no implementation / ${DIST_ID}-${DIST_VERS} (${DIST_VERSION_CODENAME})"
            ;;
    esac
}

valkey.install() {
    info_msg "installing valkey ..."
    valkey.distro.setup

    case $DIST_ID in
        debian | ubuntu)
            apt-cache show "${VALKEY_PACKAGES}" &>/dev/null || valkey.backports
            pkg_install "${VALKEY_PACKAGES}"

            # do some fix ...
            # chown -R valkey:valkey /var/log/valkey/ /var/lib/valkey/ /etc/valkey/

            # https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#PrivateUsers=
            sed -i 's/PrivateUsers=true/# PrivateUsers=true/' /lib/systemd/system/valkey-server.service
            sed -i 's/PrivateUsers=true/# PrivateUsers=true/' /lib/systemd/system/valkey-server@.service

            systemd_activate_service valkey-server
            ;;
        arch | fedora | centos)
            pkg_install "${VALKEY_PACKAGES}"
            systemd_activate_service valkey
            ;;
        *)
            # install backports if package is not in the current APT repos
            pkg_install "${VALKEY_PACKAGES}"
            ;;
    esac

    # case $DIST_ID-$DIST_VERS in
    #     arch-*|fedora-*|centos-7)
    #         systemctl enable nginx
    #         systemctl start nginx
    #         ;;
    # esac
}
