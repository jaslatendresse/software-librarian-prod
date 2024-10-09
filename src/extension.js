const fs = require('fs');
const vscode = require('vscode');
const { execFile } = require('child_process');
const path = require('path');
const os = require('os');

async function getApiKey(context) {
    const apiKeyFromEnv = process.env.API_KEY;

    // First, check if the API key is set via environment variables
    if (apiKeyFromEnv) {
        console.log("Using API key from environment variable.");
        return apiKeyFromEnv;
    }

    // Fallback to using the Secret Storage API if no environment variable is found
    console.log("Environment variable not found, checking VSCode Secret Storage...");
    
    if (!context.secrets) {
        vscode.window.showErrorMessage('Secret Storage API is not available in this version of VSCode.');
        return null;
    }

    try {
        const apiKey = await context.secrets.get('apiKey');
        if (!apiKey) {
            vscode.window.showErrorMessage('API key is not set. Please provide an API key using the command.');
            return null;
        }
        console.log("Using API key from VSCode Secret Storage.");
        return apiKey;
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to retrieve API key: ${error.message}`);
        return null;
    }
}

async function setApiKey(context) {
    // Prompt the user to enter their API key
    const apiKey = await vscode.window.showInputBox({
        prompt: "Enter your API key",
        ignoreFocusOut: true,  // Keep the input box open when focus changes
        password: true          // Hide the API key input for security
    });

    if (!apiKey) {
        vscode.window.showErrorMessage("API key input was canceled or invalid.");
        return;
    }

    try {
        // Store the API key in VSCode's Secret Storage
        await context.secrets.store('apiKey', apiKey);
        vscode.window.showInformationMessage("API key has been stored securely.");
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to store API key: ${error.message}`);
    }
}

async function activate(context) {
    console.log("Extension activated");

    let disposableSetApiKey = vscode.commands.registerCommand('pythonAnalyzer.setApiKey', async function () {
        await setApiKey(context);
    });

    context.subscriptions.push(disposableSetApiKey);

    class PythonAnalyzerProvider {
        constructor() {
            this._onDidChangeTreeData = new vscode.EventEmitter();
            this.onDidChangeTreeData = this._onDidChangeTreeData.event;
            this.results = [];
            this.originalData = [];
        }

        refresh(newResults) {
            this.results = this.results.concat(newResults.map((library, index) => ({
                id: `${library.library}-${index}-${Date.now()}`,
                label: library.library,
                tooltip: library.message,
                contextValue: 'library',
                collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
                children: this.getLibraryDetails(library)
            })));

            newResults.forEach(newLibrary => {
                const existingLibrary = this.originalData.find(lib => lib.library === newLibrary.library);
                if (!existingLibrary) {
                    this.originalData.push(newLibrary);
                }
            });

            this._onDidChangeTreeData.fire();
        }

        removeItemById(id) {
            this.results = this.results.filter(item => item.id !== id);
            const libraryName = id.split('-')[0];
            this.originalData = this.originalData.filter(item => item.library !== libraryName);
            this._onDidChangeTreeData.fire();
        }

        getTreeItem(element) {
            const treeItem = new vscode.TreeItem(element.label);
            treeItem.tooltip = element.tooltip;
            treeItem.collapsibleState = element.collapsibleState;
            treeItem.id = element.id; 
            treeItem.contextValue = element.contextValue;  
            if (element.command) {
                treeItem.command = element.command;
            }
            if (element.iconPath) {
                treeItem.iconPath = element.iconPath;
            }
            return treeItem;
        }

        getChildren(element) {
            if (!element) {
                return this.results;
            }
            return element.children || [];
        }

        getLibraryDetails(library) {
            const details = [];
            details.push({
                label: `Type: ${library.pkg_type}`,
                tooltip: `Package type: ${library.pkg_type}`,
                iconPath: library.pkg_type === 'third-party' ? new vscode.ThemeIcon('package') : new vscode.ThemeIcon('library'),
                collapsibleState: vscode.TreeItemCollapsibleState.None
            });

            details.push({
                label: `Deprecated: ${library.is_deprecated ? 'Yes' : 'No'}`,
                tooltip: `Is deprecated: ${library.is_deprecated}`,
                iconPath: library.is_deprecated ? new vscode.ThemeIcon('warning') : new vscode.ThemeIcon('check'),
                collapsibleState: vscode.TreeItemCollapsibleState.None
            });

            if (library.dependencies && library.dependencies.length > 0) {
                details.push({
                    label: `Dependencies: ${library.dependencies.join(', ')}`,
                    tooltip: `Dependencies: ${library.dependencies.join(', ')}`,
                    iconPath: new vscode.ThemeIcon('list-unordered'),
                    collapsibleState: vscode.TreeItemCollapsibleState.None
                });
            }

            if (library.age) {
                details.push({
                    label: `Age: ${library.age}`,
                    tooltip: `Library age: ${library.age}`,
                    iconPath: new vscode.ThemeIcon('calendar'),
                    collapsibleState: vscode.TreeItemCollapsibleState.None
                });
            }

            if (library.version_frequency) {
                details.push({
                    label: `Version Frequency: ${library.version_frequency}`,
                    tooltip: `Version update frequency: ${library.version_frequency}`,
                    iconPath: new vscode.ThemeIcon('sync'),
                    collapsibleState: vscode.TreeItemCollapsibleState.None
                });
            }

            if (library.license) {
                details.push({
                    label: `License: ${library.license}`,
                    tooltip: `License: ${library.license}`,
                    iconPath: new vscode.ThemeIcon('law'),
                    collapsibleState: vscode.TreeItemCollapsibleState.None
                });
            }

            details.push({
                label: library.message,
                tooltip: library.message,
                iconPath: new vscode.ThemeIcon('info'),
                collapsibleState: vscode.TreeItemCollapsibleState.None
            });

            return details;
        }
    }

    const pythonAnalyzerProvider = new PythonAnalyzerProvider();
    const treeView = vscode.window.createTreeView('pythonAnalyzerView', {
        treeDataProvider: pythonAnalyzerProvider
    });

    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = "$(sync~spin) Analyzing Python code...";
    statusBarItem.command = "pythonAnalyzer.analyzeCode";
    context.subscriptions.push(statusBarItem);

    let disposableAnalyze = vscode.commands.registerCommand('pythonAnalyzer.analyzeCode', async function (input) {
        console.log("Analyze Python Code command has been triggered.");
    
        const editor = vscode.window.activeTextEditor;
        let codeSnippet = input;
        if (!codeSnippet && editor) {
            codeSnippet = editor.document.getText(editor.selection);
        }
    
        if (!codeSnippet) {
            vscode.window.showErrorMessage('No code snippet or library list provided for analysis.');
            console.log("No code snippet or library list provided for analysis.");
            return;
        }
    
        let formattedInput = codeSnippet.trim();
    
        if (!formattedInput.includes('import') && formattedInput.split(',').length > 1) {
            const libraries = formattedInput.split(',').map(lib => lib.trim());
            formattedInput = JSON.stringify(libraries);
        }
    
        const pythonPath = getPythonPath(context.extensionPath);
        if (!pythonPath) {
            vscode.window.showErrorMessage('Could not find Python interpreter. Please ensure Python is correctly set up.');
            return;
        }
    
        // Retrieve the API key using the context object
        const apiKey = await getApiKey(context);
        if (!apiKey) {
            // Exit if the API key could not be retrieved
            vscode.window.showErrorMessage('API key is missing. Analysis cannot be performed.');
            return;
        }
    
        const env = { ...process.env, API_KEY: apiKey };
    
        const dataDirectory = context.asAbsolutePath('data');
        const packagesImportsFile = path.join(dataDirectory, 'packages_imports.csv');
        const packagesModulesFile = path.join(dataDirectory, 'packages_modules.csv');
    
        const pythonScriptPath = path.join(context.extensionPath, 'scripts', 'PythonAnalyzer.py');
        console.log("Running Python script at path:", pythonScriptPath);
    
        try {
            statusBarItem.show();
            execFile(pythonPath, [pythonScriptPath, formattedInput, packagesImportsFile, packagesModulesFile], { env }, (error, stdout, stderr) => {
                if (error) {
                    vscode.window.showErrorMessage(`Error: ${stderr || error.message}`);
                    console.log("Error occurred:", stderr || error.message);
                    return;
                }
    
                console.log("Python script output (stdout):", stdout);
    
                try {
                    const result = JSON.parse(stdout);
                    console.log("Parsed JSON output:", result);
    
                    pythonAnalyzerProvider.refresh(result);
    
                    vscode.window.showInformationMessage("Analysis complete. Check the 'Software Librarian Results' view for details.");
                } catch (err) {
                    vscode.window.showErrorMessage(`Failed to parse Python output: ${err.message}`);
                    console.log("Failed to parse Python output:", err.message);
                } finally {
                    statusBarItem.hide();
                }
            });
        } catch (err) {
            console.log("Caught exception during execFile:", err.message);
            vscode.window.showErrorMessage(`Failed to execute Python script: ${err.message}`);
        }
    });
    
    //determine the correct Python path depending on the OS
    function getPythonPath(extensionPath) {
        const venvPath = path.join(extensionPath, 'venv');
        if (os.platform() === 'win32') {
            //windows: Python is in scripts folder
            return path.join(venvPath, 'Scripts', 'python.exe');
        } else {
            //macOS/linux: Python is in bin folder
            return path.join(venvPath, 'bin', 'python');
        }
    }

    let disposableDownloadSingle = vscode.commands.registerCommand('pythonAnalyzer.downloadJsonSingle', (treeItem) => {
        const data = pythonAnalyzerProvider.originalData.find(item => item.library === treeItem.label);
        if (data) {
            const filePath = path.join(vscode.workspace.rootPath || __dirname, `${treeItem.label}.json`);
            fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
            vscode.window.showInformationMessage(`JSON downloaded for ${treeItem.label} at ${filePath}`);
        }
    });

    let disposableDownloadAll = vscode.commands.registerCommand('pythonAnalyzer.downloadJsonAll', () => {
        if (pythonAnalyzerProvider.originalData.length > 0) {
            const filePath = path.join(vscode.workspace.rootPath || __dirname, `software_librarian_results.json`);
            fs.writeFileSync(filePath, JSON.stringify(pythonAnalyzerProvider.originalData, null, 2));
            vscode.window.showInformationMessage(`All results downloaded as JSON at ${filePath}`);
        } else {
            vscode.window.showWarningMessage('No results available to download.');
        }
    });

    let disposableRemove = vscode.commands.registerCommand('pythonAnalyzer.removeResult', async (treeItem) => {
        const confirm = await vscode.window.showWarningMessage(
            `Are you sure you want to remove ${treeItem.label}?`,
            { modal: true },
            'Yes', 'No'
        );
        if (confirm == 'Yes') {
            pythonAnalyzerProvider.removeItemById(treeItem.id);
            vscode.window.showInformationMessage(`Removed: ${treeItem.label}`);
        }
    });

    let disposableClearAll = vscode.commands.registerCommand('pythonAnalyzer.removeAllResults', async () => {
        const confirm = await vscode.window.showWarningMessage(
            'Are you sure you want to clear all results?',
            { modal: true },
            'Yes', 'No'
        );
        if (confirm === 'Yes') {
            pythonAnalyzerProvider.results = [];
            pythonAnalyzerProvider._onDidChangeTreeData.fire();
            vscode.window.showInformationMessage('All results have been cleared.');
        }
    });

    context.subscriptions.push(disposableAnalyze);
    context.subscriptions.push(disposableRemove);
    context.subscriptions.push(disposableDownloadSingle);
    context.subscriptions.push(disposableDownloadAll);
    context.subscriptions.push(disposableClearAll);

    let lastImportLine = null;

    //autocompleted import statements
    vscode.workspace.onDidChangeTextDocument(event => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || event.document !== editor.document) return;

        const changes = event.contentChanges;
        for (const change of changes) {
            const changeText = change.text.trim();

            if (changeText.includes('import') && !changeText.startsWith('#') && !changeText.includes('"""') && !changeText.includes("'''")) {
                console.log("Detected an autocompleted import statement:", changeText);
                lastImportLine = editor.document.lineAt(change.range.start.line).text.trim();
            }

            //enter key press (new line creation)
            if (change.text === '\n' && lastImportLine) {
                const previousLineText = editor.document.lineAt(change.range.start.line).text.trim();

                if (previousLineText === lastImportLine) {
                    console.log("Enter pressed after import statement. Triggering analysis.");
                    vscode.commands.executeCommand('pythonAnalyzer.analyzeCode', lastImportLine);
                    lastImportLine = null;
                }
            }
        }
    });

    const statusBarButton = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 200);
    statusBarButton.command = 'pythonAnalyzer.analyzeCode';
    statusBarButton.text = "$(beaker) Analyze Python Code";
    statusBarButton.tooltip = "Analyze the selected Python code or package list";
    statusBarButton.show();
    console.log("Status bar button created and shown");

    context.subscriptions.push(statusBarButton);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
