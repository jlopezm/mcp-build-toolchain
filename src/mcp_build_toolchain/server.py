import asyncio
import subprocess
import re
import sys
import os
import locale

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("mcp-build-toolchain")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get-compilation-errors",
            description="Get errors and warning results from compilation result to evaluate by llm and apply the necessary changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "outfile": {
                        "type": "string",
                        "description": "This is the file with absolute path to get the compilation errors and warnings",
                    },
                    "regexp": {
                        "type": "string",
                        "description": "Regular expression to filter from the compilation log the warnings and errors",
                    },
                },
                "required": ["outfile"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """

    if name == "get-compilation-errors":
        
        if not arguments:
            raise ValueError("Missing arguments")

        outfile = arguments.get("outfile")
        regexp = arguments.get("regexp")

        normalized_path = outfile.replace("/", os.sep) if os.name == "nt" else outfile

        if regexp:
            regular_expression = regexp
        else:
            regular_expression = r'(?i)error\s+#|warning\s+#'

        try:
            # Detect appropriate encoding based on OS and locale
            if os.name == 'nt':
                encoding = 'cp1252'  # Windows default
            else:
                encoding = locale.getpreferredencoding(do_setlocale=True)  # Unix/OS default with locale awareness
            
            filtered_lines2 = []
            with open(normalized_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
                filtered_lines = [line.strip() for line in lines if re.search(regular_expression, line)]
                for line in lines:
                    if re.search(regular_expression, line):
                        filtered_lines2.append(line)
                
        except FileNotFoundError:
            print(f"El archivo '{outfile}' no se encontró.")
            return [
                types.TextContent(
                    type="text",
                    text=f"El archivo '{normalized_path}' no se encontró.",
                )
            ]
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"El archivo '{normalized_path}' no se encontró.",
                )
            ]

        # Notify clients that resources have changed
        # await server.request_context.session.send_resource_list_changed()

        return [
            types.TextContent(
                type="text",
                text=f"Result: '{filtered_lines}'",
            )
        ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-build-toolchain",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
