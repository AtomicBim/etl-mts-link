import requests
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from dotenv import load_dotenv
import urllib3
import ssl

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

# Registry for endpoint decorators
_endpoint_registry = {}


def endpoint(path: str):
    """Decorator to register an endpoint for an extractor function"""
    def decorator(func: Callable):
        _endpoint_registry[func.__name__] = path
        return func
    return decorator


def get_registered_endpoints() -> Dict[str, str]:
    """Get all registered endpoints"""
    return _endpoint_registry.copy()


class BaseExtractor(ABC):
    def __init__(self, config_path: str = "config/tokens.json"):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get("base_url", "https://api.mts-link.ru/v3")
        self.api_token = self.config.get("api_token")
        self.extraction_path = os.getenv("EXTRACTION_PATH", ".")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file {config_path} not found")
            return {}
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-auth-token": self.api_token,
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    @abstractmethod
    def get_endpoint(self) -> str:
        pass
    
    def get_url_params(self, **kwargs) -> Optional[Dict[str, Any]]:
        return None
    
    def extract(self, **kwargs) -> Optional[Dict[str, Any]]:
        endpoint = self.get_endpoint()
        # Separate path parameters from query parameters
        path_params = {k: v for k, v in kwargs.items() if '{' + k + '}' in endpoint}
        query_params = {k: v for k, v in kwargs.items() if '{' + k + '}' not in endpoint}
        
        if path_params:
            endpoint = endpoint.format(**path_params)
            
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        params = self.get_url_params(**query_params)
        
        print(f"Sending request to: {url}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            print("Request successful!")
            return data
            
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error: {http_err}")
            print(f"Response code: {response.status_code}")
            print(f"Response body: {response.text}")
        except requests.exceptions.RequestException as err:
            print(f"Other error: {err}")
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err}")
            print(f"Response text: {response.text}")
        
        return None
    
    def save_to_file(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            endpoint_name = self.get_endpoint().replace("/", "_").replace("{", "").replace("}", "")
            filename = f"{endpoint_name}_{timestamp}.json"
        
        filepath = os.path.join(self.extraction_path, filename)
        os.makedirs(self.extraction_path, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Data saved to: {filepath}")
        return filepath


class UniversalExtractor(BaseExtractor):
    """Universal extractor that can work with any endpoint"""
    
    def __init__(self, endpoint_path: str, config_path: str = "config/tokens.json"):
        super().__init__(config_path)
        self.endpoint_path = endpoint_path
        
    def get_endpoint(self) -> str:
        return self.endpoint_path
    
    def extract_and_save(self, filename: Optional[str] = None, **kwargs) -> Optional[str]:
        """Extract data and automatically save to file"""
        data = self.extract(**kwargs)
        if data is not None:
            return self.save_to_file(data, filename)
        return None


def run_extractor(extractor_name: str, **kwargs) -> Optional[str]:
    """Run an extractor by name using registered endpoints"""
    if extractor_name not in _endpoint_registry:
        print(f"Extractor '{extractor_name}' not found in registry")
        available = list(_endpoint_registry.keys())
        print(f"Available extractors: {available}")
        return None
    
    # Check if there's a custom function implementation
    import sys
    for module_name, module in sys.modules.items():
        if hasattr(module, extractor_name):
            func = getattr(module, extractor_name)
            if callable(func) and hasattr(func, '__name__') and func.__name__ == extractor_name:
                # Call the custom function
                try:
                    result = func(**kwargs)
                    if result is not None:
                        return result
                except Exception as e:
                    print(f"Error running custom extractor {extractor_name}: {e}")
                break

    # Fall back to universal extractor
    endpoint_path = _endpoint_registry[extractor_name]
    extractor = UniversalExtractor(endpoint_path)
    return extractor.extract_and_save(**kwargs)


