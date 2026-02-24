# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP

def initialize_informix_prompts(server: FastMCP):
    @server.prompt
    def ask_question(question: str) -> str:
        return f"You are a database expert. Answer the following question: {question} "
