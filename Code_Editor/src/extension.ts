// extension.ts - WITH HTTP SERVER FOR AGENT INTEGRATION
import * as vscode from 'vscode';
import axios from 'axios';
import * as http from 'http';

interface OllamaResponse {
  model: string;
  response: string;
  done: boolean;
}

interface EditInstruction {
  action: 'replace' | 'insert' | 'delete' | 'create';
  file?: string;
  startLine?: number;
  endLine?: number;
  content?: string;
  position?: number;
}

interface AgentRequest {
  prompt: string;
  file?: string;
  selection?: {
    start: { line: number; character: number };
    end: { line: number; character: number };
  };
}

let server: http.Server | null = null;

export function activate(context: vscode.ExtensionContext) {
  console.log('Ollama Code Editor extension is now active');

  // Start HTTP server for agent communication
  startAgentServer(context);

  // Original command for manual use
  const manualCommand = vscode.commands.registerCommand(
    'ollama-code-editor.editWithAgent',
    async () => {
      await handleManualEdit();
    }
  );

  // New command that can be called programmatically
  const programmaticCommand = vscode.commands.registerCommand(
    'ollama-code-editor.editWithPrompt',
    async (prompt: string, filePath?: string) => {
      await handleProgrammaticEdit(prompt, filePath);
    }
  );

  context.subscriptions.push(manualCommand, programmaticCommand);
}

function startAgentServer(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration('ollamaCodeEditor');
  const serverPort = config.get<number>('agentServerPort', 3000);

  server = http.createServer(async (req, res) => {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(200);
      res.end();
      return;
    }

    if (req.method === 'POST' && req.url === '/edit') {
      let body = '';
      
      req.on('data', chunk => {
        body += chunk.toString();
      });

      req.on('end', async () => {
        try {
          const request: AgentRequest = JSON.parse(body);
          
          if (!request.prompt) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Missing prompt' }));
            return;
          }

          // Execute the edit
          const result = await handleProgrammaticEdit(
            request.prompt,
            request.file,
            request.selection
          );

          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            success: true, 
            message: 'Edit applied successfully',
            result 
          }));
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            success: false, 
            error: errorMessage 
          }));
        }
      });
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
    }
  });

  server.listen(serverPort, () => {
    console.log(`Agent server listening on http://localhost:${serverPort}`);
    vscode.window.showInformationMessage(
      `Ollama Agent Server running on port ${serverPort}`
    );
  });

  context.subscriptions.push({
    dispose: () => {
      if (server) {
        server.close();
        console.log('Agent server stopped');
      }
    }
  });
}

async function handleManualEdit() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor found');
    return;
  }

  const prompt = await vscode.window.showInputBox({
    prompt: 'Enter your editing instruction',
    placeHolder: 'e.g., Add error handling to this function',
  });

  if (!prompt) {
    return;
  }

  await executeEdit(editor, prompt);
}

async function handleProgrammaticEdit(
  prompt: string,
  filePath?: string,
  selection?: { start: { line: number; character: number }; end: { line: number; character: number } }
): Promise<string> {
  let editor: vscode.TextEditor | undefined;

  if (filePath) {
    // Open the specified file
    const uri = vscode.Uri.file(filePath);
    const document = await vscode.workspace.openTextDocument(uri);
    editor = await vscode.window.showTextDocument(document);
  } else {
    // Use active editor
    editor = vscode.window.activeTextEditor;
  }

  if (!editor) {
    throw new Error('No editor available');
  }

  // Set selection if provided
  if (selection) {
    const start = new vscode.Position(selection.start.line, selection.start.character);
    const end = new vscode.Position(selection.end.line, selection.end.character);
    editor.selection = new vscode.Selection(start, end);
  }

  return await executeEdit(editor, prompt, false);
}

async function executeEdit(
  editor: vscode.TextEditor,
  prompt: string,
  showProgress: boolean = true
): Promise<string> {
  const config = vscode.workspace.getConfiguration('ollamaCodeEditor');
  const agentModel = config.get<string>('agentModel', 'llama2');
  const codingModel = config.get<string>('codingModel', 'codellama');
  const ollamaUrl = config.get<string>('ollamaUrl', 'http://localhost:11434');
  const useDedicatedCoder = config.get<boolean>('useDedicatedCoder', true);

  const progressOptions = {
    location: vscode.ProgressLocation.Notification,
    title: 'Ollama Code Editor',
    cancellable: true,
  };

  const executeTask = async (progress?: any, token?: vscode.CancellationToken) => {
    const report = (message: string) => {
      if (progress) progress.report({ message });
    };

    try {
      report('Analyzing your request...');

      const document = editor.document;
      const selection = editor.selection;
      const selectedText = document.getText(selection);
      const fullText = document.getText();
      const languageId = document.languageId;

      const contextText = selectedText || fullText;
      const agentPrompt = buildAgentPrompt(
        prompt,
        contextText,
        languageId,
        document.fileName
      );

      report('Getting editing plan from agent...');
      const agentResponse = await callOllama(
        ollamaUrl,
        agentModel,
        agentPrompt,
        token
      );

      if (!agentResponse) {
        throw new Error('No response from agent');
      }

      report('Generating code edits...');
      let editInstructions: EditInstruction[];

      if (useDedicatedCoder) {
        const codingPrompt = buildCodingPrompt(
          agentResponse,
          contextText,
          languageId
        );
        const codingResponse = await callOllama(
          ollamaUrl,
          codingModel,
          codingPrompt,
          token
        );
        editInstructions = parseEditInstructions(codingResponse, contextText);
      } else {
        editInstructions = parseEditInstructions(agentResponse, contextText);
      }

      report('Applying edits...');
      await applyEdits(editor, editInstructions);

      if (showProgress) {
        vscode.window.showInformationMessage('Code edits applied successfully!');
      }

      return 'Edit completed successfully';
    } catch (error) {
      if (token?.isCancellationRequested) {
        if (showProgress) {
          vscode.window.showInformationMessage('Operation cancelled');
        }
        throw new Error('Operation cancelled');
      } else {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        console.error('Extension error:', error);
        if (showProgress) {
          vscode.window.showErrorMessage(`Error: ${errorMessage}`);
        }
        throw error;
      }
    }
  };

  if (showProgress) {
    return await vscode.window.withProgress(progressOptions, executeTask);
  } else {
    return await executeTask();
  }
}

function buildAgentPrompt(
  userPrompt: string,
  code: string,
  language: string,
  fileName: string
): string {
  return `You are a code editing assistant. The user wants to modify their ${language} code.

File: ${fileName}
Current code:
\`\`\`${language}
${code}
\`\`\`

User request: ${userPrompt}

Please analyze this request and provide clear editing instructions. Describe what changes need to be made and provide the modified code. Format your response with the complete updated code in a code block.`;
}

function buildCodingPrompt(
  agentPlan: string,
  originalCode: string,
  language: string
): string {
  return `You are a code generation assistant. Based on the following editing plan, generate the complete modified code.

Editing plan:
${agentPlan}

Original code:
\`\`\`${language}
${originalCode}
\`\`\`

Provide the complete updated code in a single code block. Include all necessary changes while preserving the structure and style of the original code.`;
}

async function callOllama(
  baseUrl: string,
  model: string,
  prompt: string,
  token?: vscode.CancellationToken
): Promise<string> {
  let fullResponse = '';
  
  const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const apiUrl = `${cleanBaseUrl}/api/generate`;

  console.log(`Calling Ollama at: ${apiUrl} with model: ${model}`);

  try {
    const response = await axios.post(
      apiUrl,
      {
        model: model,
        prompt: prompt,
        stream: false,
      },
      {
        timeout: 120000,
        cancelToken: token ? new axios.CancelToken((cancel) => {
          token.onCancellationRequested(() => cancel('User cancelled'));
        }) : undefined,
      }
    );

    if (response.data && response.data.response) {
      return response.data.response;
    }

    throw new Error('Invalid response format from Ollama');
  } catch (error) {
    if (axios.isCancel(error)) {
      throw new Error('Request cancelled');
    }
    
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        throw new Error(
          `Ollama API endpoint not found. Please check:\n` +
          `1. Ollama is running (try: ollama serve)\n` +
          `2. Model "${model}" is installed (try: ollama pull ${model})\n` +
          `3. URL is correct: ${cleanBaseUrl}`
        );
      }
      
      const errorMsg = error.response?.data?.error || error.message;
      throw new Error(`Ollama error: ${errorMsg}`);
    }
    
    throw error;
  }
}

function parseEditInstructions(
  response: string,
  originalCode: string
): EditInstruction[] {
  const codeBlockRegex = /```(?:\w+)?\n([\s\S]*?)```/g;
  const matches = [...response.matchAll(codeBlockRegex)];

  if (matches.length > 0) {
    const newCode = matches[matches.length - 1][1].trim();
    return [
      {
        action: 'replace',
        startLine: 0,
        endLine: originalCode.split('\n').length,
        content: newCode,
      },
    ];
  }

  const lines = response.split('\n');
  const codeLines = lines.filter(
    (line) =>
      line.trim() &&
      !line.match(/^(here|this|the|i|you|we|let|based|now|first)/i) &&
      (line.includes('{') ||
        line.includes('}') ||
        line.includes('(') ||
        line.includes(';') ||
        line.includes('='))
  );

  if (codeLines.length > 0) {
    return [
      {
        action: 'replace',
        startLine: 0,
        endLine: originalCode.split('\n').length,
        content: codeLines.join('\n'),
      },
    ];
  }

  throw new Error(
    'Could not extract code from response. Please ensure the model provides code in a code block.'
  );
}

async function applyEdits(
  editor: vscode.TextEditor,
  instructions: EditInstruction[]
): Promise<void> {
  const document = editor.document;

  await editor.edit((editBuilder) => {
    for (const instruction of instructions) {
      switch (instruction.action) {
        case 'replace':
          if (
            instruction.startLine !== undefined &&
            instruction.endLine !== undefined &&
            instruction.content !== undefined
          ) {
            const startPos = new vscode.Position(instruction.startLine, 0);
            const endPos = new vscode.Position(
              instruction.endLine,
              document.lineAt(
                Math.min(instruction.endLine, document.lineCount - 1)
              ).text.length
            );
            const range = new vscode.Range(startPos, endPos);
            editBuilder.replace(range, instruction.content);
          }
          break;

        case 'insert':
          if (
            instruction.startLine !== undefined &&
            instruction.content !== undefined
          ) {
            const pos = new vscode.Position(instruction.startLine, 0);
            editBuilder.insert(pos, instruction.content + '\n');
          }
          break;

        case 'delete':
          if (
            instruction.startLine !== undefined &&
            instruction.endLine !== undefined
          ) {
            const startPos = new vscode.Position(instruction.startLine, 0);
            const endPos = new vscode.Position(instruction.endLine + 1, 0);
            const range = new vscode.Range(startPos, endPos);
            editBuilder.delete(range);
          }
          break;
      }
    }
  });

  try {
    await vscode.commands.executeCommand('editor.action.formatDocument');
  } catch (error) {
    console.log('Could not format document:', error);
  }
}

export function deactivate() {
  if (server) {
    server.close();
  }
}