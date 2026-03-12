# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP


def initialize_zen_prompts(server: FastMCP):
    @server.prompt
    def ask_question(question: str) -> str:
        """Ask a question about Zen database."""
        return f"You are a Zen (Actian PSQL) database expert. Answer the following question: {question}"
