import json


class SettingsHandler:
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.advanced_settings = self.load_current_settings()

    def load_current_settings(self) -> dict:
        with open(self.json_filename, "r") as file:
            settings_dict = json.load(file)

        advanced_settings = settings_dict["Advanced Settings"]

        return advanced_settings
    
    def update_advanced_settings(self, updated_advanced_settings: dict):
        new_dict = {
            "Advanced Settings": updated_advanced_settings
        }

        print(new_dict)

        with open(self.json_filename, "w") as file:
            json.dump(new_dict, file)

        self.advanced_settings = updated_advanced_settings

    def update_advanced_settings_param(self, key: str, new_val):
        if self.get_advanced_setting_param(key) is not None:
            update_advanced_settings_dict = self.advanced_settings
            update_advanced_settings_dict[key] = new_val
            self.update_advanced_settings(update_advanced_settings_dict)

    def get_advanced_settings(self):
        return self.advanced_settings
    
    def get_advanced_setting_param(self, key: str):
        return self.advanced_settings.get(key)


class LanguagesHandler:
    def __init__(self, json_filename):
        self.json_filename = json_filename
        self.langs = self.load_languages()

    def load_languages(self) -> list:
        with open(self.json_filename, "r") as file:
            langs = json.load(file)

        if type(langs) != list:
            raise RuntimeError("Languages must be provided as lists")
        if len(langs) < 2:
            raise RuntimeError("At least 2 languages must be supported") 

        return langs
    
    def get_supported_languages(self):
        return self.langs
    
