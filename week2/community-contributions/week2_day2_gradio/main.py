from json_handlers import SettingsHandler, LanguagesHandler
from ollama_utils import get_downloaded_models
from gradio_ui import GradioUI

settings_json = "settings.json"
languages_json = "languages.json"

if __name__ == "__main__":
    settings = SettingsHandler(settings_json)
    languages = LanguagesHandler(languages_json)

    models = get_downloaded_models()

    gradio_ui = GradioUI(models, settings, languages)
    gradio_ui.build_and_launch()
