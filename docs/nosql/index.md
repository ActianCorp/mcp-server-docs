---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian NoSQL Database

This page explains how to use the **Actian MCP Server** with **Actian NoSQL Database**.

## Overview

The Actian NoSQL MCP Server acts as a bridge between any MCP client and your Actian NoSQL Database. Once configured, clients can explore schema metadata, run read-only JPQL queries and access all details of the persistent objects retrieved.

### Capabilities

| Action | Description |
|--------|-------------|
| **Discover the Schema of a NoSQL Database** | List classes, Explore details of persistent classes |
| **Run queries on database objects** | Use Filter, Projections, Navigation |
| **Retrieve Objects by ID** | Including optimizations for collections of Object IDs |

## Configuration

There are basically just two settings you need to define in order to
configure the NSQL MCP Server.

1. The port which you want to use to connect to the MCP Server
2. The database url you want to explore with the MCP Server<br>
	The database url looks like `database@server:port#user:password`.<br>
	`port`, `user` and `password` are optional.


<!-- TODO: Describe the configuration file format and required fields for NoSQL. Example:

```json
{
  "plugins": [
    "actian_mcp_server.nosql.plugin.NoSQLPlugin"
  ],
  "nosql": {
    "host": "localhost",
    "port": 27017,
    "database": "mydb",
    "username": "admin",
    "password": "secret"
  }
}
```
-->

## Quick start

In order to start the MCP Server, you just need to run the docker image by providing the parameters specified above.

`docker run --name NSQL-MCP -e NSQL_CONNECTIONURL=cars@localhost -p 8080:8080 actian/nsql-mcp-server`

