#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later

tmpdir="/var/tmp/searxng-podman/"

container.help() {
    cat <<EOF
container.:
  build   : build container image
EOF
}

container.__get_platform() {
    local __arch="$1"

    case $__arch in
        "X64" | "x86_64" | "amd64")
            arch="amd64"
            variant=""
            platform="linux/$arch"
            ;;
        "ARM64" | "aarch64" | "arm64")
            arch="arm64"
            variant=""
            platform="linux/$arch"
            ;;
        "ARMV7" | "armhf" | "armv7l" | "armv7")
            arch="arm"
            variant="v7"
            platform="linux/$arch/$variant"
            ;;
        *)
            die 1 "unsupported architecture: $__arch"
            ;;
    esac
}

container.__import_oci() {
    required_commands podman

    local __release_tags=("$DOCKER_TAG" "latest")
    local __archives=()

    mkdir -p "$tmpdir"

    while IFS= read -r -d '' archive; do
        __archives+=("$archive")
    done < <(find "$tmpdir" -maxdepth 1 -type f -name '*.tar' -print0)

    if [ "${#__archives[@]}" -eq 0 ]; then
        die 1 "no archives found in $tmpdir"
    fi

    (
        set -e

        podman manifest rm --ignore "${__release_tags[@]/#/localhost/searxng/searxng:}"

        for tag in "${__release_tags[@]}"; do
            podman manifest create "localhost/searxng/searxng:$tag"

            for f in "${__archives[@]}"; do
                podman manifest add "localhost/searxng/searxng:$tag" "oci-archive:$f"
            done
        done

        podman manifest inspect "localhost/searxng/searxng:$DOCKER_TAG"
    )
    dump_return $?
}

container.build() {
    required_commands git

    local container_engine
    local arch
    local variant
    local platform

    # Check if podman or docker is installed
    if [ "$1" = "podman" ] || [ "$1" = "docker" ]; then
        if ! command -v "$1" &>/dev/null; then
            die 42 "$1 is not installed"
        fi
        container_engine="$1"
    else
        # If no explicit engine is passed, prioritize podman over docker
        if command -v podman &>/dev/null; then
            container_engine="podman"
        elif command -v docker &>/dev/null; then
            container_engine="docker"
        else
            die 42 "no compatible container engine is installed"
        fi
    fi
    info_msg "Selected engine: $container_engine"
    "$container_engine" version

    container.__get_platform "${OVERRIDE_ARCH:-$(uname -m)}"
    info_msg "Selected platform: $platform"

    if [ "$container_engine" = "docker" ] && ! docker buildx version &>/dev/null; then
        die 42 "docker buildx is not installed: https://docs.docker.com/go/buildx/"
    fi

    pyenv.install

    (
        set -e
        pyenv.activate

        if [ ! -d .git ]; then
            die 1 "this is not a Git repository"
        fi

        # TODO: get current branch
        if ! git remote get-url origin &>/dev/null; then
            die 1 "there is no remote origin"
        fi

        git update-index -q --refresh
        python -m searx.version freeze
        eval "$(python -m searx.version)"

        info_msg "Set \$DOCKER_TAG: $DOCKER_TAG"
        info_msg "Set \$GIT_URL: $GIT_URL"

        if [ "$container_engine" = "podman" ]; then
            params_build_builder="build --format=oci --layers --platform=$platform --identity-label=false"
            params_build="build --format=oci --layers --platform=$platform --identity-label=false"
        else
            params_build_builder="build --platform=$platform"
            params_build=$params_build_builder
        fi

        local_tag_arch="localhost/searxng/searxng:$DOCKER_TAG-$arch$variant"
        params_build+=" --tag=$local_tag_arch"
        if [ "$GITHUB_ACTIONS" != "true" ]; then
            params_build+=" --tag=localhost/searxng/searxng:latest"
            params_build+=" --tag=localhost/searxng/searxng:$DOCKER_TAG"
        fi

        # shellcheck disable=SC2086
        "$container_engine" $params_build_builder \
            --tag="localhost/searxng/searxng:builder" \
            --file="./container/builder.dockerfile" \
            .
        build_msg CONTAINER "Image \"builder\" built"

        # shellcheck disable=SC2086
        "$container_engine" $params_build \
            --build-arg="CREATED=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --build-arg="VERSION=$DOCKER_TAG" \
            --build-arg="VCS_URL=$GIT_URL" \
            --build-arg="VCS_REVISION=$(git rev-parse HEAD)" \
            --file="./container/dist.dockerfile" \
            .
        build_msg CONTAINER "Image built"

        if [ "$GITHUB_ACTIONS" = "true" ]; then
            required_commands podman

            mkdir -p "$tmpdir"
            rm -f "$tmpdir"/*.tar
            image_archive="$tmpdir/image_$arch$variant.tar"

            podman save --format=oci-archive --output="$image_archive" "$local_tag_arch"

            # Output to GHA
            cat <<EOF >>"$GITHUB_OUTPUT"
docker_tag=$DOCKER_TAG
EOF
        fi
    )
    dump_return $?
}

container.test() {
    required_commands podman

    local image="$1"

    if [ -z "$image" ]; then
        image=$(find "$tmpdir" -type f -name '*.tar' -print -quit)
        if [ -z "$image" ]; then
            die 1 "no archives found in $tmpdir"
        fi
    fi

    (
        set -e

        if [ -f "$image" ]; then
            image=$(podman load --input="$image" | sed -n 's/^Loaded image: *//p' | tail -n1)
        fi

        name="searxng-$(head -c 32 /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 16)"

        podman create --name="$name" --rm --timeout=60 --network="host" "$image" >/dev/null

        podman start "$name" >/dev/null
        podman logs -f "$name" &
        pid_logs=$!

        # Wait until container is ready
        curl -fsS --retry 30 --retry-delay 2 --retry-all-errors --max-time 5 "http://localhost:8080/healthz"

        kill $pid_logs &>/dev/null || true
        podman stop "$name" >/dev/null
    )
    dump_return $?
}

container.push() {
    required_commands podman

    local release_tags=("$DOCKER_TAG" "latest")
    local release_registries=("ghcr.io" "docker.io")

    if [ "$GITHUB_ACTIONS" != "true" ]; then
        die 1 "This command is intended to be run in Actions"
    fi

    if ! podman manifest exists "localhost/searxng/searxng:${release_tags[0]}" ||
        ! podman manifest exists "localhost/searxng/searxng:${release_tags[1]}"; then
        container.__import_oci
    fi

    (
        set -e

        podman image list

        for registry in "${release_registries[@]}"; do
            for tag in "${release_tags[@]}"; do
                build_msg CONTAINER "Pushing manifest $tag to $registry"

                podman manifest push --all \
                    "localhost/searxng/searxng:$tag" \
                    "docker://$registry/${GITHUB_REPOSITORY_OWNER:-"searxng"}/searxng:$tag"
            done
        done
    )
    dump_return $?
}

# Alias
podman.build() {
    container.build podman
}

# Alias
docker.build() {
    container.build docker
}

# Alias
docker.buildx() {
    container.build docker
}
