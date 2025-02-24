import asyncio
import subprocess
import re

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("mcp-build-toolchain")

""" @server.list_resources()
async def handle_list_resources() -> list[types.Resource]:

    # List available note resources.
    # Each note is exposed as a resource with a custom note:// URI scheme.

    return [
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ] """

""" @server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:

    # Read a specific note's content by its URI.
    # The note name is extracted from the URI host component.

    if uri.scheme != "note":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return notes[name]
    raise ValueError(f"Note not found: {name}") """

""" @server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:

    # List available prompts.
    # Each prompt can have optional arguments to customize its behavior.

    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ] """

""" 
@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:

    # Generate a prompt by combining arguments with server state.
    # The prompt includes all current notes and can be customized via arguments.

    if name != "summarize-notes":
        raise ValueError(f"Unknown prompt: {name}")

    style = (arguments or {}).get("style", "brief")
    detail_prompt = " Give extensive details." if style == "detailed" else ""

    return types.GetPromptResult(
        description="Summarize the current notes",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                    + "\n".join(
                        f"- {name}: {content}"
                        for name, content in notes.items()
                    ),
                ),
            )
        ],
    )
 """

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="build-toolchain",
            description="Use this tool to build the project when user request to build or compile",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "This is the file with absolute path to execute the build command for the toolchain",
                    },
                },
                "required": ["command"],
            },
        ),
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
    if name == "build-toolchain":

        if not arguments:
            raise ValueError("Missing arguments")

        command = arguments.get("command")

        import os

        def normalize_path(path: str) -> str:
            """Convierte las barras de un path a las correctas según el sistema operativo."""
            return path.replace("/", os.sep)

        normalized_path = command.replace("/", os.sep) if os.name == "nt" else command

        exec_dir = os.path.dirname(os.path.abspath(normalized_path))

        command_result = subprocess.run(
            [normalized_path], 
            stdout=subprocess.PIPE, 
            text=True,
            cwd=exec_dir 
            )

        # Notify clients that resources have changed
        # await server.request_context.session.send_resource_list_changed()

        return [
            types.TextContent(
                type="text",
                text=f"Result: '{command_result.stdout}'",
            )
        ]
    elif name == "get-compilation-errors":
        
        if not arguments:
            raise ValueError("Missing arguments")

        outfile = arguments.get("outfile")

        try:
            with open(outfile, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                filtered_lines = [line.strip() for line in lines if re.search(r'(?i)error|warning', line)]
                
        except FileNotFoundError:
            print(f"El archivo '{outfile}' no se encontró.")
            return [
                types.TextContent(
                    type="text",
                    text=f"El archivo '{outfile}' no se encontró.",
                )
            ]
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=f"El archivo '{outfile}' no se encontró.",
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