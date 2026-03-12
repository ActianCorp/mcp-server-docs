#!/usr/bin/env bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

require_env() {
    local var_name="$1"
    [[ -n "${!var_name:-}" ]] || {
        echo "ERROR: Environment variable '$var_name' is required." >&2
        return
    }
}

require_env II_INSTALLATION

export MCP_SERVER_ROOT="$(dirname "$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")")"
export DBMS="vector"
export DBMS_ROOT="$MCP_SERVER_ROOT/src/$DBMS"
export CONF_FILE="${CONF_FILE:-$DBMS_ROOT/conf.json}"
export MCP_SERVER_CONTAINER_IMAGE_NAME="${MCP_SERVER_CONTAINER_IMAGE_NAME:-actian/vector-mcp-server-linux}"
export MCP_SERVER_CONTAINER_VERSION="${MCP_SERVER_CONTAINER_VERSION:-1.0.0}"
export MCP_SERVER_CONTAINER_NAME="${MCP_SERVER_CONTAINER_NAME:-actian-vector-mcp-server}"
export MCP_SERVER_PORT_INSIDE_CONTAINER="${MCP_SERVER_PORT_INSIDE_CONTAINER:-"$(grep 'port' $CONF_FILE | sed -r 's/[^:]+: *(.*).*/\1/')"}"
export MCP_SERVER_PORT_OUTSIDE_CONTAINER="${MCP_SERVER_PORT_INSIDE_CONTAINER}"
export DOCKERFILE="${DOCKERFILE:-$DBMS_ROOT/docker/Dockerfile-vector}"
export DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-$DBMS_ROOT/docker/docker-compose.yml}"
export TEST_DIR="${TEST_DIR:-$DBMS_ROOT/tests}"
export TEST_DB_NAME="${TEST_DB_NAME:-"$(grep 'database' $CONF_FILE | sed -r 's/[^:]+: *\"(.*)\".*/\1/')"}"
export TEST_DB_INIT_SCRIPT="${TEST_DB_INIT_SCRIPT:-$TEST_DIR/test_db_init.sh}"


print_env() {
    cat <<EOF
Environment variables:
MCP_SERVER_ROOT=$MCP_SERVER_ROOT
DBMS=$DBMS
DBMS_ROOT=$DBMS_ROOT
MCP_SERVER_CONTAINER_IMAGE_NAME=$MCP_SERVER_CONTAINER_IMAGE_NAME
MCP_SERVER_CONTAINER_VERSION=$MCP_SERVER_CONTAINER_VERSION
MCP_SERVER_CONTAINER_NAME=$MCP_SERVER_CONTAINER_NAME
MCP_SERVER_PORT_INSIDE_CONTAINER=$MCP_SERVER_PORT_INSIDE_CONTAINER
CONF_FILE=$CONF_FILE
DOCKER_COMPOSE_FILE=$DOCKER_COMPOSE_FILE
DOCKERFILE=$DOCKERFILE
TEST_DIR=$TEST_DIR
TEST_DB_NAME=$TEST_DB_NAME
TEST_DB_INIT_SCRIPT=$TEST_DB_INIT_SCRIPT
EOF
}

build_image() {
    bash "$MCP_SERVER_ROOT/make-docker-vector.sh"
}

start_container() {
    require_env DATABASE_USER
    require_env DATABASE_PASSWORD
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d
}

stop_container() {
    docker compose -f "$DOCKER_COMPOSE_FILE" down
}

init_db() {
    require_env DATABASE_USER
    bash "$TEST_DB_INIT_SCRIPT"
}

all() {
    init_db
    build_image
    start_container
}

prompt_yes_no() {
    local prompt="$1"
    local reply

    while true; do
        read -r -p "$prompt [y/n]: " reply
        case "$reply" in
            y|Y) return 0 ;;
            n|N) return 1 ;;
            *) echo "Please enter y or n." ;;
        esac
    done
}

interactive() {
    if prompt_yes_no "Preapare database $TEST_DB_NAME?"; then
        init_db
    fi

    if prompt_yes_no "Build the container image $MCP_SERVER_CONTAINER_IMAGE_NAME:$MCP_SERVER_CONTAINER_VERSION?"; then
        build_image
    fi

    if prompt_yes_no "Start the container $MCP_SERVER_CONTAINER_NAME?"; then
        start_container
    fi
}

usage() {
    cat <<'EOF'
Usage:
  source src/vector/setup.sh
  bash src/vector/setup.sh <command>

Commands:
  --i                 Interactive mode for --all command
  --build-image       Build the Vector MCP server docker image
  --start-container   Start the Vector MCP server container
  --stop-container    Stop and remove the Vector MCP server container
  --init-db           Recreate and initialize the Vector test database
  --all               Prepare the database, build the Vector MCP Server image and start the container
  --help              Show this help message
EOF
}

main() {
    local command="${1:--help}"

    if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
        print_env
        return 0
    fi

    case "$command" in
        --i)
            interactive
            ;;
        --build-image)
            build_image
            ;;
        --start-container)
            start_container
            ;;
        --stop-container)
            stop_container
            ;;
        --init-db)
            init_db
            ;;
        --all)
            all
            ;;
        --help)
            usage
            ;;
        *)
            usage >&2
            exit 1
            ;;
    esac
}

main "$@"