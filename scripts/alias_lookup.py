import sys
sys.dont_write_bytecode = True
import pandas as pd

class PackageAliasLookup:
    def __init__(self, csv_file):
        self.package_data = pd.read_csv(csv_file)
        self.alias_to_package = self._create_alias_mapping()

    def _create_alias_mapping(self):
        alias_to_package = {}
        for _, row in self.package_data.iterrows():
            package_name = row['package_name']
            aliases = row['import_list']
            if pd.notna(aliases):
                aliases_list = eval(aliases)
                for alias in aliases_list:
                    alias = alias.strip()
                    alias_to_package[alias] = package_name
        return alias_to_package

    def get_package_name(self, alias):
        return self.alias_to_package.get(alias, None)

    def alias_exists(self, alias):
        return alias in self.alias_to_package
