#!/bin/bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

DBMS="vector"

echo
echo "Building the Actian MCP Server docker image for $DBMS"
echo

MCP_SERVER=$MCP_SERVER_ROOT/src/actian_mcp_server
PYPROJECT_FILE=$MCP_SERVER_ROOT/pyproject.toml
UVLOCK_FILE=$MCP_SERVER_ROOT/uv.lock
ACTIAN_CLIENT=$MCP_SERVER_ROOT/src/vector/actian-client.tgz
VECTOR_FEATURES=$MCP_SERVER_ROOT/src/vector/features
VECTOR_DOCKER=$MCP_SERVER_ROOT/src/vector/docker
ACTIAN_CLIENT=$MCP_SERVER_ROOT/src/vector/actian-client.tgz

if [[ ! -f "${MCP_SERVER}/server.py" ]]; then
    echo "Can't find the Actian MCP Server under ${MCP_SERVER}."
    exit 1
fi

if [[ ! -f "${PYPROJECT_FILE}" ]]; then
    echo "Can't find the pyproject.toml file under ${PYPROJECT_FILE}."
    exit 1
fi

if [[ ! -f "${UVLOCK_FILE}" ]]; then
    echo "Can't find the uv.lock file under ${UVLOCK_FILE}."
    exit 1
fi

if [[ ! -f "${VECTOR_FEATURES}/tools.py" ]]; then
    echo "Can't find the Actian MCP Server tools under ${VECTOR_FEATURES}."
    exit 1
fi

if [[ ! -f "${VECTOR_DOCKER}/Dockerfile-${DBMS}" ]]; then
    echo "Can't find the Actian MCP Server docker files under ${VECTOR_DOCKER}."
    exit 1
fi

if [[ ! -f "${ACTIAN_CLIENT}" ]]; then
    echo "Can't find the Actian Client tarball under ${ACTIAN_CLIENT}."
    exit 1
fi

if [[ -z "${CONTAINER_BASE_NAME_MCP_SERVER_LINUX}" ]]; then
    echo "CONTAINER_BASE_NAME_MCP_SERVER_LINUX not set."
    exit 1
fi

if [[ -z "${CONTAINER_VERSION_MCP_SERVER_LINUX}" ]]; then
    echo "CONTAINER_VERSION_MCP_SERVER_LINUX not set."
    exit 1
fi

STAGE="/tmp/docker-stage"

rm -rf $STAGE
mkdir -p $STAGE
mkdir $STAGE/src
mkdir $STAGE/vector
mkdir $STAGE/vector/features
mkdir $STAGE/vector/docker

cp -r $MCP_SERVER $STAGE/src
cp -r $VECTOR_FEATURES/* $STAGE/vector/features
cp -r $VECTOR_DOCKER/* $STAGE/vector/docker
cp $ACTIAN_CLIENT $STAGE
cp $PYPROJECT_FILE $STAGE
cp $UVLOCK_FILE $STAGE

pushd $STAGE
docker build . -f vector/docker/Dockerfile-$DBMS -t $CONTAINER_BASE_NAME_MCP_SERVER_LINUX:$CONTAINER_VERSION_MCP_SERVER_LINUX
popd
