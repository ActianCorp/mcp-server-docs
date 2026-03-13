#!/bin/bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

ACTIAN_INSTALL_DIR="${HOME}/ActianClient"
INGRES_DIR="${ACTIAN_INSTALL_DIR}/ingres"
# Instance id 'AC' is hardcoded in the Dockerfile during Actian Client installation.
ENV_SCRIPT="${INGRES_DIR}/.ingACsh"

if [[ ! -f "${ENV_SCRIPT}" ]]; then
	echo "ERROR: Expected environment script not found at '${ENV_SCRIPT}' after Actian client installation"
	exit 1
fi

# Export the required ODBC-related environment variables before loading the Actian client environment.
echo 'export ODBCSYSINI=$II_SYSTEM/ingres/files' >> "${ENV_SCRIPT}"
echo 'export ODBCINI=$II_SYSTEM/ingres/files/odbcinst.ini' >> "${ENV_SCRIPT}"
echo 'export II_ODBC_WCHAR_SIZE=2' >> "${ENV_SCRIPT}"

# Load the Actian client environment
echo "Loading the Actian client environment from '${ENV_SCRIPT}'"
. ${ENV_SCRIPT} || {
	echo "ERROR: Failed to execute '${ENV_SCRIPT}'"
	exit 1
}

exec "$@"
