#!/usr/bin/env bash
# -*- coding: utf-8; mode: sh indent-tabs-mode: nil -*-
# SPDX-License-Identifier: AGPL-3.0-or-later

# shellcheck source=utils/lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
source_dot_config
# shellcheck source=utils/brand.env
source "${REPO_ROOT}/utils/brand.env"

# load environment of the LXC suite
LXC_ENV="${LXC_ENV:-${REPO_ROOT}/utils/lxc-searx.env}"
source "$LXC_ENV"
lxc_set_suite_env

# ----------------------------------------------------------------------------
# config
# ----------------------------------------------------------------------------
#
# read also:
# - https://lxd.readthedocs.io/en/latest/

LXC_HOST_PREFIX="${LXC_HOST_PREFIX:-test}"

# Location in the container where all folders from HOST are mounted
LXC_SHARE_FOLDER="/share"
LXC_REPO_ROOT="${LXC_SHARE_FOLDER}/$(basename "${REPO_ROOT}")"

ubu1804_boilerplate="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y
apt-get install -y git curl wget
"
ubu1904_boilerplate="$ubu1804_boilerplate"

# shellcheck disable=SC2034
ubu2004_boilerplate="
$ubu1904_boilerplate
echo 'Set disable_coredump false' >> /etc/sudo.conf
"

# shellcheck disable=SC2034
ubu2110_boilerplate="$ubu1904_boilerplate"

# shellcheck disable=SC2034
archlinux_boilerplate="
pacman --noprogressbar -Syu --noconfirm
pacman --noprogressbar -S --noconfirm inetutils git curl wget sudo
echo 'Set disable_coredump false' >> /etc/sudo.conf
"

# shellcheck disable=SC2034
fedora35_boilerplate="
dnf update -y
dnf install -y git curl wget hostname
echo 'Set disable_coredump false' >> /etc/sudo.conf
"

# shellcheck disable=SC2034
centos7_boilerplate="
yum update -y
yum install -y git curl wget hostname sudo which
echo 'Set disable_coredump false' >> /etc/sudo.conf
"

REMOTE_IMAGES=()
CONTAINERS=()
LOCAL_IMAGES=()

for ((i=0; i<${#LXC_SUITE[@]}; i+=2)); do
    REMOTE_IMAGES=("${REMOTE_IMAGES[@]}" "${LXC_SUITE[i]}")
    CONTAINERS=("${CONTAINERS[@]}" "${LXC_HOST_PREFIX}-${LXC_SUITE[i+1]}")
    LOCAL_IMAGES=("${LOCAL_IMAGES[@]}" "${LXC_SUITE[i+1]}")
done

HOST_USER="${SUDO_USER:-$USER}"
HOST_USER_ID=$(id -u "${HOST_USER}")
HOST_GROUP_ID=$(id -g "${HOST_USER}")

# ----------------------------------------------------------------------------
usage() {
# ----------------------------------------------------------------------------
    _cmd="$(basename "$0")"
    cat <<EOF
usage::
  $_cmd build        [containers|<name>]
  $_cmd copy         [images]
  $_cmd remove       [containers|<name>|images]
  $_cmd [start|stop] [containers|<name>]
  $_cmd show         [images|suite|info|config [<name>]]
  $_cmd cmd          [--|<name>] '...'
  $_cmd install      [suite|base [<name>]]

build
  :containers:   build, launch all containers and 'install base' packages
  :<name>:       build, launch container <name>  and 'install base' packages
copy:
  :images:       copy remote images of the suite into local storage
remove
  :containers:   delete all 'containers' or only <container-name>
  :images:       delete local images of the suite
start/stop
  :containers:   start/stop all 'containers' from the suite
  :<name>:       start/stop container <name> from suite
show
  :info:         show info of all (or <name>) containers from LXC suite
  :config:       show config of all (or <name>) containers from the LXC suite
  :suite:        show services of all (or <name>) containers from the LXC suite
  :images:       show information of local images
cmd
  use single qoutes to evaluate in container's bash, e.g.: 'echo \$(hostname)'
  --             run command '...' in all containers of the LXC suite
  :<name>:       run command '...' in container <name>
install
  :base:         prepare LXC; install basic packages
  :suite:        install LXC ${LXC_SUITE_NAME} suite into all (or <name>) containers

EOF
    usage_containers
    [ -n "${1+x}" ] &&  err_msg "$1"
}

usage_containers() {
    lxc_suite_install_info
    [ -n "${1+x}" ] &&  err_msg "$1"
}

lxd_info() {

    cat <<EOF

LXD is needed, to install run::

  snap install lxd
  lxd init --auto

EOF
}

main() {

    local exit_val
    local _usage="unknown or missing $1 command $2"

    # don't check prerequisite when in recursion
    if [[ ! $1 == __* ]] && [[ ! $1 == --help  ]]; then
        if ! in_container; then
            ! required_commands lxc && lxd_info && exit 42
        fi
        [[ -z $LXC_SUITE ]] && err_msg "missing LXC_SUITE" && exit 42
    fi

    case $1 in
        --getenv)  var="$2"; echo "${!var}"; exit 0;;
        -h|--help) usage; exit 0;;

        build)
            sudo_or_exit
            case $2 in
                ${LXC_HOST_PREFIX}-*) build_container "$2" ;;
                ''|--|containers) build_all_containers ;;
                *) usage "$_usage"; exit 42;;
            esac
            ;;
        copy)
            case $2 in
                ''|images) lxc_copy_images_localy;;
                *) usage "$_usage"; exit 42;;
            esac
            ;;
        remove)
            sudo_or_exit
            case $2 in
                ''|--|containers) remove_containers ;;
                images) lxc_delete_images_localy ;;
                ${LXC_HOST_PREFIX}-*)
                    ! lxc_exists "$2" && warn_msg "container not yet exists: $2" && exit 0
                    if ask_yn "Do you really want to delete container $2"; then
                        lxc_delete_container "$2"
                    fi
                    ;;
                *) usage "uknown or missing container <name> $2"; exit 42;;
            esac
            ;;
        start|stop)
            sudo_or_exit
            case $2 in
                ''|--|containers)  lxc_cmd "$1" ;;
                ${LXC_HOST_PREFIX}-*)
                    ! lxc_exists "$2" && usage_containers "unknown container: $2" && exit 42
                    info_msg "lxc $1 $2"
                    lxc "$1" "$2" | prefix_stdout "[${_BBlue}${i}${_creset}] "
                    ;;
                *) usage "uknown or missing container <name> $2"; exit 42;;
            esac
            ;;
        show)
            sudo_or_exit
            case $2 in
                suite)
                    case $3 in
                        ${LXC_HOST_PREFIX}-*)
                            lxc exec -t "$3" -- "${LXC_REPO_ROOT}/utils/lxc.sh" __show suite \
                                | prefix_stdout "[${_BBlue}$3${_creset}]  "
                        ;;
                        *) show_suite;;
                    esac
                    ;;
                images) show_images ;;
                config)
                    case $3 in
                        ${LXC_HOST_PREFIX}-*)
                            ! lxc_exists "$3" && usage_containers "unknown container: $3" && exit 42
                            lxc config show "$3" | prefix_stdout "[${_BBlue}${3}${_creset}] "
                        ;;
                        *)
                            rst_title "container configurations"
                            echo
                            lxc list "$LXC_HOST_PREFIX-"
                            echo
                            lxc_cmd config show
                            ;;
                    esac
                    ;;
                info)
                    case $3 in
                        ${LXC_HOST_PREFIX}-*)
                            ! lxc_exists "$3" && usage_containers "unknown container: $3" && exit 42
                            lxc info "$3" | prefix_stdout "[${_BBlue}${3}${_creset}] "
                            ;;
                        *)
                            rst_title "container info"
                            echo
                            lxc_cmd info
                            ;;
                    esac
                    ;;
                *) usage "$_usage"; exit 42;;
            esac
            ;;
        __show)
            # wrapped show commands, called once in each container
            case $2 in
                suite) lxc_suite_info ;;
            esac
            ;;
        cmd)
            sudo_or_exit
            shift
            case $1 in
                --) shift; lxc_exec "$@" ;;
                ${LXC_HOST_PREFIX}-*)
                    ! lxc_exists "$1" && usage_containers "unknown container: $1" && exit 42
                    local name=$1
                    shift
                    lxc_exec_cmd "${name}" "$@"
                    ;;
                *) usage_containers "unknown container: $1" && exit 42
           esac
            ;;
        install)
            sudo_or_exit
            case $2 in
                suite|base)
                    case $3 in
                        ${LXC_HOST_PREFIX}-*)
                            ! lxc_exists "$3" && usage_containers "unknown container: $3" && exit 42
                            lxc_exec_cmd "$3" "${LXC_REPO_ROOT}/utils/lxc.sh" __install "$2"
                            ;;
                        ''|--) lxc_exec "${LXC_REPO_ROOT}/utils/lxc.sh" __install "$2" ;;
                        *) usage_containers "unknown container: $3" && exit 42
                    esac
                    ;;
                *) usage "$_usage"; exit 42 ;;
            esac
            ;;
        __install)
            # wrapped install commands, called once in each container
            # shellcheck disable=SC2119
            case $2 in
                suite) lxc_suite_install ;;
                base) FORCE_TIMEOUT=0 lxc_install_base_packages ;;
            esac
            ;;
        doc)
            echo
            echo ".. generic utils/lxc.sh documentation"
            ;;
        -*) usage "unknown option $1"; exit 42;;
        *)  usage "unknown or missing command $1"; exit 42;;
    esac
}


build_all_containers() {
    rst_title "Build all LXC containers of suite"
    echo
    usage_containers
    lxc_copy_images_localy
    lxc_init_all_containers
    lxc_config_all_containers
    lxc_boilerplate_all_containers
    rst_title "install LXC base packages" section
    echo
    lxc_exec "${LXC_REPO_ROOT}/utils/lxc.sh" __install base
    echo
    lxc list "$LXC_HOST_PREFIX"
}

build_container() {
    rst_title "Build container $1"

    local remote_image
    local container
    local image
    local boilerplate_script

    for ((i=0; i<${#LXC_SUITE[@]}; i+=2)); do
        if [ "${LXC_HOST_PREFIX}-${LXC_SUITE[i+1]}" = "$1" ]; then
            remote_image="${LXC_SUITE[i]}"
            container="${LXC_HOST_PREFIX}-${LXC_SUITE[i+1]}"
            image="${LXC_SUITE[i+1]}"
            boilerplate_script="${image}_boilerplate"
            boilerplate_script="${!boilerplate_script}"
            break
        fi
    done
    echo
    if [ -z "$container" ]; then
        err_msg "container $1 unknown"
        usage_containers
        return 42
    fi
    lxc_image_copy "${remote_image}" "${image}"
    rst_title "init container" section
    lxc_init_container "${image}" "${container}"
    rst_title "configure container" section
    lxc_config_container "${container}"
    rst_title "run LXC boilerplate scripts" section
    lxc_install_boilerplate "${container}" "$boilerplate_script"
    echo
    rst_title "install LXC base packages" section
    lxc_exec_cmd "${container}" "${LXC_REPO_ROOT}/utils/lxc.sh" __install base \
        | prefix_stdout "[${_BBlue}${container}${_creset}] "
    echo
    lxc list "$container"
}

remove_containers() {
    rst_title "Remove all LXC containers of suite"
    rst_para "existing containers matching ${_BGreen}$LXC_HOST_PREFIX-*${_creset}"
    echo
    lxc list "$LXC_HOST_PREFIX-"
    echo -en "\\n${_BRed}LXC containers to delete::${_creset}\\n\\n  ${CONTAINERS[*]}\\n" | $FMT
    local default=Ny
    [[ $FORCE_TIMEOUT = 0 ]] && default=Yn
    if ask_yn "Do you really want to delete these containers" $default; then
        for i in "${CONTAINERS[@]}"; do
            lxc_delete_container "$i"
        done
    fi
    echo
    lxc list "$LXC_HOST_PREFIX-"
}

# images
# ------

lxc_copy_images_localy() {
    rst_title "copy images" section
    for ((i=0; i<${#LXC_SUITE[@]}; i+=2)); do
        lxc_image_copy "${LXC_SUITE[i]}" "${LXC_SUITE[i+1]}"
    done
    # lxc image list local: && wait_key
}

lxc_delete_images_localy() {
    rst_title "Delete LXC images"
    rst_para "local existing images"
    echo
    lxc image list local:
    echo -en "\\n${_BRed}LXC images to delete::${_creset}\\n\\n  ${LOCAL_IMAGES[*]}\\n"
    if ask_yn "Do you really want to delete these images"; then
        for i in "${LOCAL_IMAGES[@]}"; do
            lxc_delete_local_image "$i"
        done
    fi

    for i in $(lxc image list --format csv | grep '^,' | sed 's/,\([^,]*\).*$/\1/'); do
        if ask_yn "Image $i has no alias, do you want to delete the image?" Yn; then
            lxc_delete_local_image "$i"
        fi
    done

    echo
    lxc image list local:
}

show_images(){
    rst_title "local images"
    echo
    lxc image list local:
    echo -en "\\n${_Green}LXC suite images::${_creset}\\n\\n  ${LOCAL_IMAGES[*]}\\n"
    wait_key
    for i in "${LOCAL_IMAGES[@]}"; do
        if lxc_image_exists "$i"; then
            info_msg "lxc image info ${_BBlue}${i}${_creset}"
            lxc image info "$i" | prefix_stdout "[${_BBlue}${i}${_creset}] "
        else
            warn_msg "image ${_BBlue}$i${_creset} does not yet exists"
        fi
    done

}


# container
# ---------

show_suite(){
    rst_title "LXC suite ($LXC_HOST_PREFIX-*)"
    echo
    lxc list "$LXC_HOST_PREFIX-"
    echo
    for i in "${CONTAINERS[@]}"; do
        if ! lxc_exists "$i"; then
            warn_msg "container ${_BBlue}$i${_creset} does not yet exists"
        else
            lxc exec -t "${i}" -- "${LXC_REPO_ROOT}/utils/lxc.sh" __show suite \
                | prefix_stdout "[${_BBlue}${i}${_creset}]  "
            echo
        fi
    done
}

lxc_cmd() {
    for i in "${CONTAINERS[@]}"; do
        if ! lxc_exists "$i"; then
            warn_msg "container ${_BBlue}$i${_creset} does not yet exists"
        else
            info_msg "lxc $* $i"
            lxc "$@" "$i" | prefix_stdout "[${_BBlue}${i}${_creset}] "
        fi
    done
}

lxc_exec_cmd() {
    local name="$1"
    shift
    exit_val=
    info_msg "[${_BBlue}${name}${_creset}] ${_BGreen}${*}${_creset}"
    lxc exec -t --cwd "${LXC_REPO_ROOT}" "${name}" -- bash -c "$*"
    exit_val=$?
    if [[ $exit_val -ne 0 ]]; then
        warn_msg "[${_BBlue}${name}${_creset}] exit code (${_BRed}${exit_val}${_creset}) from ${_BGreen}${*}${_creset}"
    else
        info_msg "[${_BBlue}${name}${_creset}] exit code (${exit_val}) from ${_BGreen}${*}${_creset}"
    fi
}

lxc_exec() {
    for i in "${CONTAINERS[@]}"; do
        if ! lxc_exists "$i"; then
            warn_msg "container ${_BBlue}$i${_creset} does not yet exists"
        else
            lxc_exec_cmd "${i}" "$@" | prefix_stdout "[${_BBlue}${i}${_creset}] "
        fi
    done
}

lxc_init_all_containers() {
    rst_title "init all containers" section

    local image_name
    local container_name

    for ((i=0; i<${#LXC_SUITE[@]}; i+=2)); do
        lxc_init_container "${LXC_SUITE[i+1]}" "${LXC_HOST_PREFIX}-${LXC_SUITE[i+1]}"
    done
}

lxc_config_all_containers() {
    rst_title "configure all containers" section

    for i in "${CONTAINERS[@]}"; do
        lxc_config_container "${i}"
    done
}

lxc_config_container() {
    info_msg "[${_BBlue}$1${_creset}] configure container ..."

    info_msg "[${_BBlue}$1${_creset}] map uid/gid from host to container"
    # https://lxd.readthedocs.io/en/latest/userns-idmap/#custom-idmaps
    echo -e -n "uid $HOST_USER_ID 0\\ngid $HOST_GROUP_ID 0"\
        | lxc config set "$1" raw.idmap -

    info_msg "[${_BBlue}$1${_creset}] share ${REPO_ROOT} (repo_share) from HOST into container"
    # https://lxd.readthedocs.io/en/latest/instances/#type-disk
    lxc config device add "$1" repo_share disk \
        source="${REPO_ROOT}" \
        path="${LXC_REPO_ROOT}" &>/dev/null
    # lxc config show "$1" && wait_key
}

lxc_boilerplate_all_containers() {
    rst_title "run LXC boilerplate scripts" section

    local boilerplate_script
    local image_name

    for ((i=0; i<${#LXC_SUITE[@]}; i+=2)); do

        image_name="${LXC_SUITE[i+1]}"
        boilerplate_script="${image_name}_boilerplate"
        boilerplate_script="${!boilerplate_script}"

        lxc_install_boilerplate "${LXC_HOST_PREFIX}-${image_name}" "$boilerplate_script"

        if [[ -z "${boilerplate_script}" ]]; then
            err_msg "[${_BBlue}${container_name}${_creset}] no boilerplate for image '${image_name}'"
        fi
    done
}

lxc_install_boilerplate() {

    # usage:  lxc_install_boilerplate <container-name> <string: shell commands ..>
    #
    # usage:  lxc_install_boilerplate searx-archlinux "${archlinux_boilerplate}"

    local container_name="$1"
    local boilerplate_script="$2"

    info_msg "[${_BBlue}${container_name}${_creset}] init .."
    if lxc start -q "${container_name}" &>/dev/null; then
        sleep 5 # guest needs some time to come up and get an IP
    fi
    if ! check_connectivity "${container_name}"; then
        die 42 "Container ${container_name} has no internet connectivity!"
    fi
    lxc_init_container_env "${container_name}"
    info_msg "[${_BBlue}${container_name}${_creset}] install /.lxcenv.mk .."
    cat <<EOF | lxc exec "${container_name}" -- bash | prefix_stdout "[${_BBlue}${container_name}${_creset}] "
rm -f "/.lxcenv.mk"
ln -s "${LXC_REPO_ROOT}/utils/makefile.lxc" "/.lxcenv.mk"
ls -l "/.lxcenv.mk"
EOF

    info_msg "[${_BBlue}${container_name}${_creset}] run LXC boilerplate scripts .."
    if lxc start -q "${container_name}" &>/dev/null; then
        sleep 5 # guest needs some time to come up and get an IP
    fi
    if [[ -n "${boilerplate_script}" ]]; then
        echo "${boilerplate_script}" \
            | lxc exec "${container_name}" -- bash \
            | prefix_stdout "[${_BBlue}${container_name}${_creset}] "
    fi
}

check_connectivity() {
    local ret_val=0
    info_msg "check internet connectivity ..."
    if ! lxc exec "${1}" -- ping -c 1 8.8.8.8 &>/dev/null; then
        ret_val=1
        err_msg "no internet connectivity!"
        info_msg "Most often the connectivity is blocked by a docker installation:"
        info_msg "Whenever docker is started (reboot) it sets the iptables policy "
        info_msg "for the FORWARD chain to DROP, see:"
        info_msg "    https://docs.searxng.org/utils/lxc.sh.html#internet-connectivity-docker"
        iptables-save | grep ":FORWARD"
    fi
    return $ret_val
}

# ----------------------------------------------------------------------------
main "$@"
# ----------------------------------------------------------------------------
