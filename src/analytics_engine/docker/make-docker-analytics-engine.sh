#!/bin/bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

echo
echo "Building the Actian MCP Server docker image for $DBMS"
echo

MCP_SERVER=$MCP_SERVER_ROOT/src/actian_mcp_server
PYPROJECT_FILE=$MCP_SERVER_ROOT/pyproject.toml
UVLOCK_FILE=$MCP_SERVER_ROOT/uv.lock
ACTIAN_CLIENT=$DBMS_ROOT/actian-client.tgz
MCP_SERVER_FEATURES=$DBMS_ROOT/features
MCP_SERVER_DOCKER=$DBMS_ROOT/docker
MCP_SERVER_PLUGIN=$DBMS_ROOT/plugin.py

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

if [[ ! -f "${MCP_SERVER_FEATURES}/tools.py" ]]; then
    echo "Can't find the Actian MCP Server tools under ${MCP_SERVER_FEATURES}."
    exit 1
fi

if [[ ! -f "${MCP_SERVER_PLUGIN}" ]]; then
    echo "Can't find the Analytics Engine plugin under ${MCP_SERVER_PLUGIN}."
    exit 1
fi

if [[ ! -f "${MCP_SERVER_DOCKER}/Dockerfile-analytics-engine" ]]; then
    echo "Can't find the Actian MCP Server docker files under ${MCP_SERVER_DOCKER}."
    exit 1
fi

if [[ ! -f "${ACTIAN_CLIENT}" ]]; then
    echo "Can't find the Actian Client tarball under ${ACTIAN_CLIENT}."
    exit 1
fi

if [[ -z "${MCP_SERVER_CONTAINER_IMAGE_NAME}" ]]; then
    echo "MCP_SERVER_CONTAINER_IMAGE_NAME not set."
    exit 1
fi

if [[ -z "${MCP_SERVER_CONTAINER_VERSION}" ]]; then
    echo "MCP_SERVER_CONTAINER_VERSION not set."
    exit 1
fi

STAGE="/tmp/docker-stage"

rm -rf $STAGE
mkdir -p $STAGE
mkdir -p $STAGE/src/actian_mcp_server
mkdir $STAGE/$DBMS
mkdir $STAGE/$DBMS/features
mkdir $STAGE/$DBMS/docker

cp $MCP_SERVER/__init__.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER/oauth.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER/plugin.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER/server_interfaces.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER/server_utils.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER/server.py $STAGE/src/actian_mcp_server
cp $MCP_SERVER_PLUGIN $STAGE/$DBMS/plugin.py
cp $MCP_SERVER_FEATURES/tools.py $STAGE/$DBMS/features
cp $MCP_SERVER_FEATURES/resources.py $STAGE/$DBMS/features
cp $MCP_SERVER_FEATURES/prompts.py $STAGE/$DBMS/features
cp $MCP_SERVER_FEATURES/instructions.py $STAGE/$DBMS/features
cp $MCP_SERVER_DOCKER/Dockerfile-analytics-engine $STAGE/$DBMS/docker
cp $MCP_SERVER_DOCKER/entrypoint.sh $STAGE/$DBMS/docker
cp $ACTIAN_CLIENT $STAGE
cp $PYPROJECT_FILE $STAGE
cp $UVLOCK_FILE $STAGE

pushd $STAGE
docker build . -f $DBMS/docker/Dockerfile-analytics-engine -t $MCP_SERVER_CONTAINER_IMAGE_NAME:$MCP_SERVER_CONTAINER_VERSION
popd
