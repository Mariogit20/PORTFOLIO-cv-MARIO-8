import threading

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

from .models import HistoriqueUser
from .services import purge_old_history

_local = threading.local()


def get_current_user():
    """Retourne l'utilisateur courant stocké dans le thread local (si présent)."""
    return getattr(_local, "user", None)


def _get_client_ip(request) -> str:
    """
    Récupère l'IP client de manière simple.
    Si tu es derrière un proxy, adapte la logique X-Forwarded-For selon ta config.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # "client, proxy1, proxy2"
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or ""


class HistoriqueCurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _local.user = None

        # Récupération user depuis la session (structure supposée)
        user_session = request.session.get("user")
        if user_session and isinstance(user_session, dict) and user_session.get("id"):
            from app_contact.models import User
            _local.user = User.objects.filter(id=user_session["id"]).first()

        # Purge automatique max 1 fois par jour par session
        today_key = f"hist_purge_{timezone.now().date().isoformat()}"
        if not request.session.get(today_key):
            purge_old_history()
            request.session[today_key] = True

    def process_response(self, request, response):
        """
        Log READ : lecture d'une page (GET) pour TOUTES les pages visitées
        (connecté OU non), en excluant les assets et les endpoints internes
        de l'historique.
        """
        try:
            # Uniquement les lectures de pages (GET)
            if request.method != "GET":
                return response

            # Optionnel : ne logger que si la réponse est "OK" (évite 404/500)
            if getattr(response, "status_code", 200) >= 400:
                return response

            path = (request.path or "")
            lowered = path.lower()

            # Exclure static/media/favicon (sinon spam)
            if lowered.startswith("/static/") or lowered.startswith("/media/") or lowered == "/favicon.ico":
                return response

            # Exclure les endpoints de l'historique (sinon l'historique s'auto-log)
            # D'après ton projet : /fragment/ (GET) et /settings/ (POST)
            if lowered.startswith("/fragment/") or lowered.startswith("/settings/"):
                return response

            # Recommandé : ne logger que les pages HTML (évite AJAX/JSON)
            accept = (request.headers.get("Accept") or "").lower()
            if accept and "text/html" not in accept:
                return response

            # User connecté ou None
            user = getattr(_local, "user", None)

            # Assurer une session_key même pour les non connectés
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key or ""

            user_agent = (request.META.get("HTTP_USER_AGENT") or "").strip()
            ip = _get_client_ip(request)

            # IMPORTANT : request.get_full_path() n'inclut jamais "#fragment"
            full_path = request.get_full_path() or path

            details = (
                "Lecture (GET) d'une page"
                f" | session_key={session_key}"
                f" | user_agent={user_agent}"
            )

            HistoriqueUser.objects.create(
                user=user,  # None si non connecté
                action="READ",
                app_label="ui",
                model_name="page",
                object_id="",
                object_repr=path[:255],
                url=full_path[:255],
                method=request.method,
                ip=ip[:64],
                details=details
            )
        except Exception:
            # Ne jamais casser l'affichage à cause du logging
            pass

        return response
