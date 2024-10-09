import sys
import ast
import json
from get_type import TypeGetter
from alias_lookup import PackageAliasLookup
from get_metadata import Metadata
from placeholder_lookup import PlaceholderLookup
from module_lookup import PackageModuleLookup

class PythonAnalyzer:
    def __init__(self, packages_imports_file, packages_modules_file):
        """
        Initialize the PythonAnalyzer with paths to the packages imports and modules files.
        """
        self.type_getter = TypeGetter()
        self.alias_lookup = PackageAliasLookup(packages_imports_file)
        self.module_lookup = PackageModuleLookup(packages_modules_file)
        self.metadata = Metadata()
        self.placeholder_lookup = PlaceholderLookup()

    def extract_libraries_from_code(self, code_snippet):
        """
        Parses the code snippet and extracts all imported libraries.
        """
        code_snippet = code_snippet.strip()
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError:
            raise ValueError('Invalid input.')

        libraries = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    libraries.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                libraries.add(node.module.split('.')[0])

        return list(libraries)

    def process_code(self, code_snippet=None, libraries=None):
        if code_snippet:
            try:
                libraries = self.extract_libraries_from_code(code_snippet)
            except ValueError as e:
                return {'error': str(e)}

            if not libraries:
                return {'message': 'No import statements found in the provided code snippet.'}

        if not libraries:
            return {'message': 'No valid input provided.'}

        results = []

        for library in libraries:
            pkg_type = self.type_getter.diagnose(library)
            library_info = {'library': library}

            if pkg_type == 'standard':
                is_deprecated = self.type_getter.check_deprecation(library)
                library_info.update({
                    'pkg_type': pkg_type,
                    'is_deprecated': is_deprecated,
                    'message': f'https://docs.python.org/3/library/{library}.html',
                })

            elif pkg_type == 'third-party':
                is_deprecated = self.type_getter.check_deprecation(library)
                is_placeholder = self.placeholder_lookup.check_placeholder(library)

                dependencies = self.metadata.get_dependencies(library)
                age = self.metadata.get_age(library)
                version_frequency = self.metadata.get_version_frequency(library)
                source_rank = self.metadata.get_source_rank(library)
                dependents = self.metadata.get_dependents(library)
                license = self.metadata.get_license(library)

                library_info.update({
                    'pkg_type': pkg_type,
                    'is_deprecated': is_deprecated,
                    'dependencies': dependencies,
                    'age': age,
                    'version_frequency': version_frequency,
                    'source_rank': source_rank,
                    'dependents': dependents,
                    'license': license,
                    'message': is_placeholder if is_placeholder else f'https://pypi.org/project/{library}/'
                })

            elif pkg_type == 'invalid':
                is_alias = self.alias_lookup.alias_exists(library)
                is_module = self.module_lookup.module_exists(library)
                is_placeholder = self.placeholder_lookup.check_placeholder(library)

                if not is_alias and not is_module and is_placeholder is None:
                    library_info['message'] = 'Library not found.'
                else:
                    if is_alias:
                        pkg_from_alias = self.alias_lookup.get_package_name(library)

                        library_info = {'library': pkg_from_alias}

                        pkg_type = self.type_getter.diagnose(pkg_from_alias)

                        is_deprecated = self.type_getter.check_deprecation(pkg_from_alias)
                        dependencies = self.metadata.get_dependencies(pkg_from_alias)
                        age = self.metadata.get_age(pkg_from_alias)
                        version_frequency = self.metadata.get_version_frequency(pkg_from_alias)
                        source_rank = self.metadata.get_source_rank(pkg_from_alias)
                        dependents = self.metadata.get_dependents(pkg_from_alias)
                        license = self.metadata.get_license(pkg_from_alias)

                        library_info.update({
                            'message': f'{library} is an alias for {pkg_from_alias}.',
                            'pkg_type': pkg_type,
                            'is_deprecated': is_deprecated,
                            'dependencies': dependencies,
                            'age': age,
                            'version_frequency': version_frequency,
                            'source_rank': source_rank,
                            'dependents': dependents,
                            'license': license
                        })

                    if is_module:
                        pkg_from_module = self.module_lookup.get_package_name(library)

                        library_info = {'library': pkg_from_module}

                        pkg_type = self.type_getter.diagnose(pkg_from_module)
                        is_deprecated = self.type_getter.check_deprecation(pkg_from_module)
                        dependencies = self.metadata.get_dependencies(pkg_from_module)
                        age = self.metadata.get_age(pkg_from_module)
                        version_frequency = self.metadata.get_version_frequency(pkg_from_module)
                        source_rank = self.metadata.get_source_rank(pkg_from_module)
                        dependents = self.metadata.get_dependents(pkg_from_module)
                        license = self.metadata.get_license(pkg_from_module)

                        library_info.update({
                            'message': f'{library} is a module for {pkg_from_module}.',
                            'pkg_type': pkg_type,
                            'is_deprecated': is_deprecated,
                            'dependencies': dependencies,
                            'age': age,
                            'version_frequency': version_frequency,
                            'source_rank': source_rank,
                            'dependents': dependents,
                            'license': license
                        })

            results.append(library_info)

        return results


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Insufficient arguments. Expected: code_snippet, packages_imports_file, packages_modules_file.")
        sys.exit(1)

    input_code_snippet = sys.argv[1]
    packages_imports_file = sys.argv[2]
    packages_modules_file = sys.argv[3]

    analyzer = PythonAnalyzer(packages_imports_file, packages_modules_file)
    result = analyzer.process_code(code_snippet=input_code_snippet)
    print(json.dumps(result))
