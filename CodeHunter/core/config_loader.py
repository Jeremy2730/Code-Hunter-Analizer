import yaml
from pathlib import Path


DEFAULT_CONFIG = {
    "analysis": {
        "ignored_numbers": [0, 1, -1],
        "magic_number_ignore_contexts": ["range", "len"]
    }
}


def load_config(project_path: str) -> dict:
    """
    Carga .codehunter.yml si existe
    """

    config_path = Path(project_path) / ".codehunter.yml"

    if not config_path.exists():
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)

        if not user_config:
            return DEFAULT_CONFIG

        return merge_configs(DEFAULT_CONFIG, user_config)

    except Exception:
        return DEFAULT_CONFIG


def merge_configs(default: dict, user: dict) -> dict:
    """
    Mezcla config por defecto con config del usuario
    """

    result = default.copy()

    for key, value in user.items():
        if isinstance(value, dict) and key in result:
            result[key].update(value)
        else:
            result[key] = value

    return result