from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException
from typing import Optional
import structlog

from src.config import settings

log = structlog.get_logger()


class LDAPUser:
    def __init__(self, data: dict):
        self.object_id: str = data.get("objectGUID", "")
        self.username: str = data.get("sAMAccountName", "")
        self.email: str = data.get("mail", "")
        self.display_name: str = data.get("displayName", "")
        self.groups: list[str] = data.get("memberOf", [])

    def is_member_of(self, group_dn: str) -> bool:
        return any(
            g.lower() == group_dn.lower() for g in self.groups
        )


def authenticate(username: str, password: str) -> Optional[LDAPUser]:
    """
    Autentica usuário no AD e retorna seus atributos.
    Retorna None se credenciais inválidas.
    """
    user_upn = f"{username}@{settings.LDAP_DOMAIN}"

    try:
        server = Server(settings.LDAP_SERVER, get_info=ALL)
        conn = Connection(
            server,
            user=user_upn,
            password=password,
            authentication=NTLM if "\\" in username else "SIMPLE",
            auto_bind=True,
        )
    except LDAPException as e:
        log.info("ldap.auth.failed", username=username, reason=str(e))
        return None

    try:
        conn.search(
            search_base=settings.LDAP_BASE_DN,
            search_filter=f"(sAMAccountName={username})",
            search_scope=SUBTREE,
            attributes=[
                "objectGUID",
                "sAMAccountName",
                "mail",
                "displayName",
                "memberOf",
            ],
        )

        if not conn.entries:
            log.warning("ldap.user.not_found", username=username)
            return None

        entry = conn.entries[0]

        # objectGUID vem como bytes — converter para string hex
        guid_raw = entry["objectGUID"].value
        if isinstance(guid_raw, bytes):
            import uuid
            object_guid = str(uuid.UUID(bytes_le=guid_raw))
        else:
            object_guid = str(guid_raw)

        groups = entry["memberOf"].values if "memberOf" in entry else []

        user_data = {
            "objectGUID": object_guid,
            "sAMAccountName": str(entry["sAMAccountName"]),
            "mail": str(entry["mail"]) if "mail" in entry else f"{username}@{settings.LDAP_DOMAIN}",
            "displayName": str(entry["displayName"]) if "displayName" in entry else username,
            "memberOf": [str(g) for g in groups],
        }

        log.info("ldap.auth.success", username=username)
        return LDAPUser(user_data)

    except LDAPException as e:
        log.error("ldap.search.error", username=username, error=str(e))
        return None
    finally:
        conn.unbind()
