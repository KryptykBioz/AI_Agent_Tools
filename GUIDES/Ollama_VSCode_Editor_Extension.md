# Ollama Code Editor Extension

A VS Code extension that integrates with local Ollama models to provide AI-powered code editing capabilities. This extension allows you to describe code changes in natural language, and the agent will intelligently modify your code.

## Features

- **Natural Language Editing**: Describe what you want to change in plain English
- **Two-Stage Processing**: Uses an agent model to understand intent and optionally a dedicated coding model to generate precise code
- **Local & Private**: All processing happens on your local Ollama instance
- **Context-Aware**: Understands your current code and makes intelligent modifications
- **Multiple Model Support**: Configure different models for planning and code generation

## Prerequisites

1. **Ollama**: Install Ollama from [ollama.ai](https://ollama.ai)
2. **Models**: Pull at least one model, e.g.:
   ```bash
   ollama pull llama2
   ollama pull codellama
   ```

## Installation

1. Clone or download this repository
2. Open the folder in VS Code
3. Run `npm install` to install dependencies
4. Press `F5` to open a new VS Code window with the extension loaded

## Usage

### Basic Usage

1. Open a code file in VS Code
2. Select the code you want to edit (optional - if nothing is selected, the entire file will be used as context)
3. Press `Ctrl+Shift+O` (or `Cmd+Shift+O` on Mac) or run the command "Edit with Ollama Agent"
4. Enter your editing instruction, such as:
   - "Add error handling to this function"
   - "Convert this to use async/await"
   - "Add TypeScript types"
   - "Refactor this code to be more readable"
   - "Add JSDoc comments"

### Example Prompts

- **Add features**: "Add input validation to this function"
- **Refactor**: "Split this large function into smaller helper functions"
- **Fix issues**: "Fix the error handling in this code"
- **Improve quality**: "Make this code more efficient"
- **Add documentation**: "Add comprehensive comments explaining what this does"
- **Convert syntax**: "Convert this from callbacks to promises"

## Configuration

Open VS Code settings and search for "Ollama Code Editor" to configure:

### `ollamaCodeEditor.agentModel`
- **Default**: `llama2`
- **Description**: The model used to understand your request and plan edits
- **Recommended models**: `llama2`, `mistral`, `mixtral`

### `ollamaCodeEditor.codingModel`
- **Default**: `codellama`
- **Description**: The specialized model used for generating code
- **Recommended models**: `codellama`, `deepseek-coder`, `phind-codellama`

### `ollamaCodeEditor.ollamaUrl`
- **Default**: `http://localhost:11434`
- **Description**: The URL of your local Ollama server

### `ollamaCodeEditor.useDedicatedCoder`
- **Default**: `true`
- **Description**: When enabled, uses a two-stage process where the agent model plans the edits and the coding model generates the code. When disabled, uses only the agent model.

## How It Works

1. **User Input**: You provide a natural language description of the changes you want
2. **Context Gathering**: The extension captures your current code, language, and selection
3. **Agent Analysis**: The agent model analyzes your request and creates an editing plan
4. **Code Generation** (optional): If using a dedicated coder, it generates the precise code changes
5. **Application**: The extension applies the edits to your document
6. **Formatting**: Automatically formats the document after changes

## Architecture

### Two-Stage Processing (Recommended)
```
User Prompt → Agent Model (planning) → Coding Model (generation) → Code Edits
```

### Single-Stage Processing
```
User Prompt → Agent Model → Code Edits
```

## Tips for Best Results

1. **Be specific**: Instead of "improve this", try "add error handling and input validation"
2. **Use context**: Select the specific code you want modified rather than entire files
3. **Choose the right model**: Use specialized coding models like `codellama` for better code generation
4. **Iterate**: You can run multiple edits sequentially to refine the code
5. **Review changes**: Always review the AI-generated changes before committing

## Troubleshooting

### "No response from agent"
- Ensure Ollama is running: `ollama serve`
- Check that the model is downloaded: `ollama list`
- Verify the Ollama URL in settings

### "Could not extract code from response"
- Try using a dedicated coding model (enable `useDedicatedCoder`)
- Use more specific prompts
- Try a different model that's better at code generation

### Slow response times
- Use smaller models for faster responses
- Consider using only the agent model (disable `useDedicatedCoder`)
- Ensure your system has adequate resources

## Recommended Model Combinations

| Use Case | Agent Model | Coding Model |
|----------|-------------|--------------|
| Fast, general edits | `llama2` | `codellama` |
| High quality | `mixtral` | `deepseek-coder` |
| Lightweight | `mistral` | `codellama:7b` |
| Python-focused | `llama2` | `codellama:python` |

## Development

### Project Structure
```
.
├── src/
│   └── extension.ts       # Main extension code
├── package.json           # Extension manifest
├── tsconfig.json         # TypeScript configuration
└── README.md            # This file
```

### Building
```bash
npm install
npm run compile
```

### Testing
Press `F5` in VS Code to open an Extension Development Host window.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Future Enhancements

- Multi-file editing support
- Diff preview before applying changes
- Conversation history
- Custom prompt templates
- Integration with version control
- Undo/redo specific AI edits


================================================================================
SETUP INSTRUCTIONS
================================================================================

1. Create folder structure:
   ollama-code-editor/
   ├── src/
   │   └── extension.ts
   ├── package.json
   ├── tsconfig.json
   └── README.md

2. Copy the content from each section above into the corresponding file

3. Install dependencies:
   npm install

4. Install Ollama models:
   ollama pull llama2
   ollama pull codellama

5. Press F5 in VS Code to test the extension

6. Use Ctrl+Shift+O (Cmd+Shift+O on Mac) to activate in any code file