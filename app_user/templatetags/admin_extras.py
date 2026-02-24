from django import template

register = template.Library()


@register.simple_tag
def check_access(role_id, menu_id, acces_existants):
    """
    Retourne True si "roleId_menuId" est présent dans acces_existants.
    Sert à cocher les cases dans la matrice Rôles x Menus.
    """
    key = f"{role_id}_{menu_id}"
    return key in (acces_existants or [])


@register.filter
def get_item(dictionary, key):
    """
    Accès sûr à dictionary.get(key, []) dans les templates.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []


@register.filter
def extract_session_key(details: str) -> str:
    """
    Extrait session_key=... depuis details format :
    "Lecture ... | session_key=XXX | user_agent=YYY"
    """
    if not details:
        return ""
    marker = "session_key="
    if marker not in details:
        return ""
    value = details.split(marker, 1)[1]
    return value.split("|", 1)[0].strip()


@register.filter
def extract_user_agent(details: str) -> str:
    """
    Extrait user_agent=... depuis details format :
    "Lecture ... | session_key=XXX | user_agent=YYY"
    """
    if not details:
        return ""
    marker = "user_agent="
    if marker not in details:
        return ""
    value = details.split(marker, 1)[1]
    return value.split("|", 1)[0].strip()
