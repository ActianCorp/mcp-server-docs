#!/bin/bash
# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

destroydb "$TEST_DB_NAME" || true
createdb -u"$DATABASE_USER" "$TEST_DB_NAME"
sql -u"$DATABASE_USER" "$TEST_DB_NAME" < "$TEST_DIR/test_tbl_init.sql"
