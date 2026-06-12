_lang = {}

def set_language(lang_dict):
    global _lang
    _lang = lang_dict

def t(key):
    return _lang.get(key, key)
