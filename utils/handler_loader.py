import importlib
import os
from telegram.ext import Application

def load_handlers(app: Application, handler_paths: list):
    for path in handler_paths:
        base_path = os.path.join(os.path.dirname(__file__), "..", path)
        for file_name in os.listdir(base_path):
            if file_name.endswith(".py") and not file_name.startswith("__"):
                module_path = f"{path}.{file_name[:-3]}"
                module = importlib.import_module(module_path)

                if hasattr(module, "get_handler"):
                    handler = module.get_handler()
                    app.add_handler(handler)