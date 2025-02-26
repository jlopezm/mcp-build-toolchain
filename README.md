# mcp-build-toolchain MCP Server

Advanced build toolchain with compilation error analysis and filtering capabilities

The objective of the MCP is minimize use of tokens to allow LLM model to process the warning and errors of compilation process and fix.
So some build log result could result so big to be sent to model. 

Using Clinerules can send information to specific project and what to do with results.
Also can use a second file where warning and/or errors can be added to avoid the model to try to fix them.

## Key Components

### MCP Tool: get-compilation-errors

```mermaid
graph TD
    A[get-compilation-errors] --> B[Analyzes build output]
    B --> C[Extracts errors/warnings]
    C --> D[Filters using .clinerules]
    D --> E[Provides structured results]
```

Key features:
- Processes raw compilation logs into structured data
- Integrates with .clinerules for targeted filtering
- Prioritizes critical errors first
- Generates actionable remediation steps

### .clinerules Configuration

Create `.clinerules` in project root to control error handling:

Describe how to compile and how to react to the different errors/warnings:

- When is requested to compile and fix the error se bellow description
- Command to compile
- Use mcp server tool 'get-compilation-errors' to get the list of warnings and errors.
- After getting the errors and warnings try to fix them and compile again. Repeat the operation 5 times until no errores are reported.
- Check `docs/avoidable_errors.md` and do nothing with errors or warning reported in this file.

### Error Documentation

Maintain `docs/avoidable_errors.md` with common issues:

```markdown
## Avoidable Warnings
- W0611: Unused import → Remove unused packages
- E302: Expected 2 blank lines → Follow PEP8 spacing

## Ignorable Errors  
- E266: Too many leading '#' → Style preference
- W504: Line break after binary operator → Project-specific
```

## Configuration

```json
"mcpServers": {
  "mcp-build-toolchain": {
    "command": "uv",
    "args": [
      "--directory",
      "/Users/joaquinlopez/mcp/mcp-build-toolchain",
      "run",
      "mcp-build-toolchain"
    ],
    "tools": {
      "get-compilation-errors": {
        "outfile": "build/errors.log"
      }
    }
  }
}
```

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-build-toolchain": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/joaquinlopez/mcp/mcp-build-toolchain",
        "run",
        "mcp-build-toolchain"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "mcp-build-toolchain": {
      "command": "uvx",
      "args": [
        "mcp-build-toolchain"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /Users/joaquinlopez/mcp/mcp-build-toolchain run mcp-build-toolchain
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
