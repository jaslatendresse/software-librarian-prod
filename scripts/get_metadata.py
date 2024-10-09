import sys
sys.dont_write_bytecode = True
import requests
import json
from datetime import datetime
import os

class Metadata: 
    def __init__(self): 
        self.api_key = os.getenv('API_KEY')
        self.metadata_cache = {}
        self.license_categories = {"Permissive": ["Artistic", "ZPL", "AFL", "CNRI", "MIT", "Apache", "BSD", "ISC", "ZLIB"], 
                      "Copyleft": ["GPL", "AGPL", "LGPL", "wxWindows"],
                      "Public Domain": ["CC0", "Unlicense"],
                      "Weak Copyleft": ["MPL", "EPL"],
                      "Non-standard": ["WTFPL"],
                      "Proprietary": ["Proprietary"],
                      "Commercial": ["Commercial"],
                      "Other": ["Other/Proprietary"]
                      }

    def fetch_metadata(self, package):
        if package in self.metadata_cache:
            return self.metadata_cache[package]
        
        url = f"https://libraries.io/api/pypi/{package}"
        params = {"api_key": self.api_key}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            metadata = response.json()
            self.metadata_cache[package] = metadata
            return metadata
        else:
            return None
    
    def get_dependencies(self, package):
        metadata = self.fetch_metadata(package)
        dependencies = []
        if metadata is not None:
            latest_version = metadata['versions'][-1]
            if latest_version is not None:
                version_number = latest_version['number']
                url = f'https://libraries.io/api/pypi/{package}/{version_number}/dependencies?api_key={self.api_key}'
                response = requests.get(url)
                if response.status_code == 200:
                    dependencies = response.json()['dependencies']
                    return len(dependencies)
        else:
            None
    
    def get_age(self, package):
        metadata = self.fetch_metadata(package)
        reference_date = datetime.now()
        if metadata is not None:
            versions_data = metadata.get('versions', [])
            if versions_data: 
                first_version = versions_data[0]
                first_version_published_at = first_version.get('published_at', '')
                age_months = (reference_date - datetime.strptime(first_version_published_at, '%Y-%m-%dT%H:%M:%S.%fZ')).days / 30
                return f"{age_months:.1f} months"
        return None
    
    def get_version_frequency(self, package):
        metadata = self.fetch_metadata(package)
        reference_date = datetime.now()
        version_frequency = 0
        if metadata is not None:
            versions_data = metadata.get('versions', [])
            number_of_versions = len(versions_data)
            first_version = versions_data[0]
            first_version_published_at = first_version.get('published_at', '')
            age_months = (reference_date - datetime.strptime(first_version_published_at, '%Y-%m-%dT%H:%M:%S.%fZ')).days / 30
            version_frequency = number_of_versions / age_months
            return f"{version_frequency:.1f} versions/month"
        else:
            return None
    
    def get_source_rank(self, package):
        metadata = self.fetch_metadata(package)
        if metadata is not None:
            return metadata.get('rank', 'N/A')
        else:
            return None
        
    def get_dependents(self, package):
        metadata = self.fetch_metadata(package)
        if metadata is not None:
            return metadata.get('dependents_count', 'N/A')
        else:
            return None
        
    def get_license(self, package):
        url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            classifiers = data.get('info', {}).get('classifiers', [])
            for classifier in classifiers:
                if 'license' in str(classifier).lower():
                    license_name = classifier.split(' :: ')[-1]
                    category = self.get_license_category(license_name)
                    return f"{license_name}, {category}"
            return f"License unspecified for package '{package}'."
        else:
            return None
    
    def get_license_category(self, license_name):
        for category, licenses in self.license_categories.items():
            for license in licenses:
                if license.lower() in license_name.lower():
                    return category
        return "Unknown"
