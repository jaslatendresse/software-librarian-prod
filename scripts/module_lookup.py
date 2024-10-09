import sys
sys.dont_write_bytecode = True
import pandas as pd

class PackageModuleLookup:
    def __init__(self, csv_file):
        self.package_data = pd.read_csv(csv_file, on_bad_lines='skip')
        self.module_to_packages = self._create_module_mapping()

    def _create_module_mapping(self):
        module_to_packages = {}
        for _, row in self.package_data.iterrows():
            package_name = row['package_name']
            modules = row['module_list']
            if pd.notna(modules):
                modules = eval(modules)
                for module in modules:
                    module = module.strip()
                    module_to_packages[module] = package_name
        return module_to_packages

    def get_package_name(self, module):
        return self.module_to_packages.get(module, None)
    
    def module_exists(self, module):
        return module in self.module_to_packages
