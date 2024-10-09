import sys
sys.dont_write_bytecode = True
import requests
import re

class PlaceholderLookup:
    def __init__(self):
        # List of placeholder keywords to detect
        self.placeholder_keywords = [
            "placeholder", "sample", "example", "test", "dummy", "temp", "package", "model",
            "lib", "module", "template", "my", "your", "name", "app", "element", "other", "data",
            "file", "parent", "child", "content", "context", "sub", "folder", "refactoring", "post",
            "mock", "component", "foo", "bar", "foobar"
        ]
    
    @staticmethod
    def fetch_pypi_package_info(package_name):
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    
    @staticmethod
    def fetch_pypi_downloads(package_name):
        url = f"https://pypistats.org/api/packages/{package_name}/recent"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['data']['last_month']  # Fetching download stats for the last month
        return 0
    
    @staticmethod
    def normalize_placeholder(name):
        return name.lower().replace("-", "").replace("_", "")
    
    def check_placeholder(self, package_name):
        download_threshold = 1000
        normalized_library_name = PlaceholderLookup.normalize_placeholder(package_name)
        
        # Create a regex pattern to match placeholder keywords with optional numbers or suffixes/prefixes
        placeholder_pattern = r"(?<!\w)({})(\d*|\W*)".format("|".join(self.placeholder_keywords))
        is_placeholder = bool(re.search(placeholder_pattern, normalized_library_name))
        
        if not is_placeholder:
            return None
        
        # Check the actual library details on PyPI if identified as a potential placeholder
        package_info = self.fetch_pypi_package_info(package_name)

        if package_info is not None:
            downloads = self.fetch_pypi_downloads(package_name)
            if downloads >= download_threshold:
                return (f"'{package_name}' is commonly used as a placeholder, but in this context,\n"
                        f"it is most likely used as a real library with {downloads} downloads in the last month.\n"
                        f"https://pypi.org/project/{package_name}/")
            else:
                return (f"'{package_name}' is a real package (https://pypi.org/project/{package_name}), but also commonly used as a placeholder. "
                        f"In this context, it is most likely used as a placeholder.")
        else:
            return f"'{package_name}' is not a valid library, but it could be used a placeholder in this context."
