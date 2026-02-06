#!/bin/bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

ACTIAN_INSTALL_DIR="${HOME}/ActianClient"
INGRES_DIR="${ACTIAN_INSTALL_DIR}/ingres"
INGVW_SH="${INGRES_DIR}/.ingVWsh"

# Path to the Actian client installer inside the image.
# NOTE: Make sure the project root containing actian-client under src/vector/actian-client
#       is copied to /app in Dockerfile.
CLIENT_INSTALL_SCRIPT="/app/src/vector/actian-client/client_install.sh"

if [[ ! -x "${CLIENT_INSTALL_SCRIPT}" ]]; then
	echo "ERROR: Actian client installer not found or not executable at '${CLIENT_INSTALL_SCRIPT}'"
	exit 1
fi

# Install the Actian client
echo "Installing Actian client into '${ACTIAN_INSTALL_DIR}'"
"${CLIENT_INSTALL_SCRIPT}" -express -acceptlicense VW -noroot "${ACTIAN_INSTALL_DIR}"

if [[ ! -f "${INGVW_SH}" ]]; then
	echo "ERROR: Expected environment script not found at '${INGVW_SH}' after Actian client installation"
	exit 1
fi

# Export the required ODBC-related environment variables before loading the Actian client environment.
echo 'export ODBCSYSINI=$II_SYSTEM/ingres/files' >> "${INGVW_SH}"
echo 'export ODBCINI=$II_SYSTEM/ingres/files/odbcinst.ini' >> "${INGVW_SH}"
echo 'export II_ODBC_WCHAR_SIZE=2' >> "${INGVW_SH}"

# Load the Actian client environment
echo "Loading the Actian client environment from '${INGVW_SH}'"
. ${INGVW_SH} || {
	echo "ERROR: Failed to execute '${INGVW_SH}'"
	exit 1
}

exec "$@"
