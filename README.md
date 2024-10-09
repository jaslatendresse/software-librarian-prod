# The Software Librarian

This VSCode extension analyzes Python packages generated in GitHub Copilot code completions and provides detailed information about each package. The extension supports macOS, Linux, and Windows platforms. 

## Features

* Automatically detects import statements and extracts Python packages from GitHub Copilot code completions. 
* Provides details about each package, including: 
    * Package type (standard, third-party)
    * Deprecation status
    * Metadata of third-party libraries (retrieved dynamically)
        * Age (months)
        * Number of dependencies
        * Number of dependents
        * Version frequency (per month)
        * SourceRank (from libraries.io)
        * License details (including the license type)
* Integrates with a bundled virtual environment to manage Python dependencies
* Can download JSON reports of analyzed packages
* Can detect whether an import statement may be using a placeholder rather than an actual package
* Can map package aliases to their distribution names, as well as package modules/subpackages to their parent package
    * **Note** Some information may be missing from the current database

## Setting Up Your API Key

To use the full functionality of the Software Librarian, you'll need to set your API key. First, retrieve your API key from [libraries.io](https://libraries.io/api).

Then, you'll need to store your key in **VSCode Secrete Storage**.

1. Open VSCode. 
2. Open the command palette (`Ctrl + Shift + P` for Windows/Linux or `Cmd + Shift + P` for macOS).
3. Type "Set API KEY" and select the command. 
4. Enter your API key and press "Enter".


## Running in Development Mode

1. Clone the repository and open it in VSCode
```
git clone https://github.com/jaslatendresse/software-librarian-prod.git
cd software-librarian-prod
code .
```

2. Install Node.js dependencies
```
npm install
```

3. Create a virtual environment inside the project directory
* On macOS/Linux:
```
python3 -m venv venv
source venv/bin/activate
```
* On Windows:
```
python -m venv venv
venv\Scripts\activate
```

4. Install Python dependencies
```
pip install -r requirements.txt
```

5. Run the extension in development move 
* Press `F5` or open the command palette (`Ctrl + Shift + P` or `Cmd + Shift + P`) and select "Run Extension".
* This will launch a new VSCode window with the extension loaded in development mode.

6. Test the extension
* Have Copilot generate code for you that contains import statements, or
* Open a Python file and select a code snippet that includes `import` statements and press the "Analyze Python Code" in the status bar (bottom left of the editor).


## Folder Structure

```
software-librarian-prod/
├── data/                       # Internal database
│   ├── packages_imports.csv
│   └── packages_modules.csv
├── scripts/                    # Python script and modules for the analysis
│   ├── PythonAnalyzer.py
│   ├── get_type.py
│   ├── alias_lookup.py
│   ├── placeholder_lookup.py
│   └── module_lookup.py
├── venv/                       # Virtual environment
│   ├── bin/                    # (macOS/Linux)
│   ├── Scripts/                # (Windows)
│   └── ...
├── src/                        # VSCode extension source files
├── package.json                # VSCode extension manifest
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## Dependencies
* Node.js: For running the VSCode extension in development mode.
* Python 3.x: For running the analysis scripts.



    