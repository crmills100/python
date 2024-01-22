import json

class Config:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.read_configuration()

    def read_configuration(self):
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_file}' not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in the configuration file.")
            return None

    def get_web_service_url(self):
        return self.config.get('web_service_url')
    
    