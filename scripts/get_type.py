import sys
sys.dont_write_bytecode = True
import stdlib_list
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import venv
import os
import subprocess

class TypeGetter: 
    def __init__(self): 
        pass

    def diagnose(self, package):
        standard_libraries = stdlib_list.stdlib_list()
        if package in standard_libraries:
            return f"standard"
        else:
            session = requests.Session()
            retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            response = session.get(f"https://pypi.org/pypi/{package}/json")
            if response.status_code == 200:
                return f"third-party"
        return f"invalid"
    
    def check_deprecation(self, package):
        url = f"https://docs.python.org/3/library/{package}.html"
        response = requests.get(url)
        response_url = response.request.url
        result = False

        #for standard libraries
        if response.status_code == 200:
            if package not in response_url:
                result = True
            else:
                result = False
        else:
            if response.status_code == 404:
                url = f"https://docs.python.org/2/library/{package}.html"
                response = requests.get(url)
                response_url = response.request.url
                if response.status_code == 200:
                    result = True
                else:
                    result = False
        
        #for third-party libraries
        if result == False:
            env_dir = f"/tmp/venv/{package}"
            venv.create(env_dir, with_pip=True)
            pip_install_command = f"{env_dir}/bin/pip install {package}"
            python_executable = "bin/python" 
        
            try:
                result = subprocess.run(pip_install_command, shell=True, capture_output=True, text=True, executable='/bin/bash')
                output = result.stdout + result.stderr

                if "deprecat" in output.lower():
                    result = True
                else:
                    import_check_command = os.path.join(env_dir, python_executable)
                    import_code = f"import warnings; warnings.simplefilter('always'); import {package}; print('Import Successful')"
                    result = subprocess.run([import_check_command, "-c", import_code], capture_output=True, text=True)
                    output_import = result.stdout + result.stderr
                    if "import successful" in output_import.lower() and "deprecat" in output_import.lower():
                        result = True
                    else:
                        result = False
            finally:
                subprocess.run(f"rm -rf {env_dir}", shell=True, executable='/bin/bash')
            return result

