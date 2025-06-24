#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

valkey.distro.setup() {
    # shellcheck disable=SC2034

    case $DIST_ID in
        ubuntu|debian|arch|fedora|centos)
            VALKEY_PACKAGES="valkey"
            ;;
        *)
            err_msg "$DIST_ID: valkey not yet implemented"
            ;;
    esac
}

valkey.install(){
    info_msg "installing valkey ..."
    valkey.distro.setup
    pkg_install "${VALKEY_PACKAGES}"
    # case $DIST_ID-$DIST_VERS in
    #     arch-*|fedora-*|centos-7)
    #         systemctl enable nginx
    #         systemctl start nginx
    #         ;;
    # esac
}
