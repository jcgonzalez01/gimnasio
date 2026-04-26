"""
Constantes de ISAPI Hikvision.
Basado en isapiEndpoints.js
"""

class ISAPI_NS:
    SYSTEM = "/ISAPI/System"
    ACCESS = "/ISAPI/AccessControl"
    EVENT = "/ISAPI/Event/notification"
    FACE_LIB = "/ISAPI/Intelligent/FDLib"
    FACE_ANALYSIS = "/ISAPI/SDT/Face"
    SECURITY = "/ISAPI/Security"
    SECURITY_CP = "/ISAPI/SecurityCP"
    VIDEO_INTERCOM = "/ISAPI/VideoIntercom"
    CONTENT_MGMT = "/ISAPI/ContentMgmt"
    STREAMING = "/ISAPI/Streaming"


# ─────────────────────────────────────────────────────────────
# SYSTEM ENDPOINTS
# ─────────────────────────────────────────────────────────────
SYSTEM = {
    "CAPABILITIES": "GET /ISAPI/System/capabilities",
    "DEVICE_INFO": "GET /ISAPI/System/deviceInfo",
    "FIRMWARE_CODE": "GET /ISAPI/System/firmwareCodeV2",
    "DEVICE_LANGUAGE": "GET /ISAPI/System/DeviceLanguage",
    "SET_DEVICE_LANGUAGE": "PUT /ISAPI/System/DeviceLanguage",
    "USER_MANUAL_LINK": "GET /ISAPI/System/GetUserManualLink",
    "ACTIVATE": "PUT /ISAPI/System/activate",
    "FACTORY_RESET": "PUT /ISAPI/System/factoryReset",
    "REBOOT": "PUT /ISAPI/System/reboot",
    "TIME": "GET /ISAPI/System/time",
    "SET_TIME": "PUT /ISAPI/System/time",
    "TIME_CAPABILITIES": "GET /ISAPI/System/time/capabilities",
    "TIME_TIMEZONE": "GET /ISAPI/System/time/timeZone",
    "SET_TIMEZONE": "PUT /ISAPI/System/time/timeZone",
    "NTP_SERVERS": "GET /ISAPI/System/time/ntpServers",
    "SET_NTP_SERVERS": "PUT /ISAPI/System/time/ntpServers",
    "NTP_CONFIG": "GET /ISAPI/System/time/ntp",
    "SET_NTP_CONFIG": "PUT /ISAPI/System/time/ntp",
    "UPGRADE_FIRMWARE": "POST /ISAPI/System/updateFirmware",
    "UPGRADE_STATUS": "GET /ISAPI/System/upgradeStatus",
    "NETWORK_CAPABILITIES": "GET /ISAPI/System/Network/capabilities",
    "SSH": "PUT /ISAPI/System/Network/ssh",
}

# ─────────────────────────────────────────────────────────────
# SECURITY ENDPOINTS
# ─────────────────────────────────────────────────────────────
SECURITY = {
    "CAPABILITIES": "GET /ISAPI/Security/capabilities",
    "CHALLENGE": "POST /ISAPI/Security/challenge",
}

# ─────────────────────────────────────────────────────────────
# EVENT / ARMING ENDPOINTS
# ─────────────────────────────────────────────────────────────
EVENT = {
    "ALERT_STREAM": "GET /ISAPI/Event/notification/alertStream",
    "SUBSCRIBE_CAP": "GET /ISAPI/Event/notification/subscribeEventCap",
    "SUBSCRIBE": "POST /ISAPI/Event/notification/subscribeEvent",
    "HTTP_HOSTS_GET": "GET /ISAPI/Event/notification/httpHosts",
    "HTTP_HOSTS_SET": "PUT /ISAPI/Event/notification/httpHosts",
}

# ─────────────────────────────────────────────────────────────
# ACCESS CONTROL ENDPOINTS
# ─────────────────────────────────────────────────────────────
ACCESS = {
    "CAPABILITIES": "GET /ISAPI/AccessControl/capabilities",
    "USER_COUNT": "GET /ISAPI/AccessControl/UserInfo/Count",
    "USER_SEARCH": "POST /ISAPI/AccessControl/UserInfo/Search",
    "USER_APPLY": "PUT /ISAPI/AccessControl/UserInfo/SetUp",
    "USER_ADD": "POST /ISAPI/AccessControl/UserInfo/Record",
    "USER_MODIFY": "PUT /ISAPI/AccessControl/UserInfo/Modify",
    "USER_DELETE": "PUT /ISAPI/AccessControl/UserInfoDetail/Delete",
    "CARD_COUNT": "GET /ISAPI/AccessControl/CardInfo/Count",
    "CARD_SEARCH": "POST /ISAPI/AccessControl/CardInfo/Search",
    "CARD_ADD": "POST /ISAPI/AccessControl/CardInfo/Record",
    "CARD_MODIFY": "PUT /ISAPI/AccessControl/CardInfo/Modify",
    "CARD_DELETE": "PUT /ISAPI/AccessControl/CardInfo/Delete",
    "FP_COUNT": "GET /ISAPI/AccessControl/FingerPrint/Count",
    "FP_ADD": "POST /ISAPI/AccessControl/FingerPrintDownload",
    "FP_DELETE": "PUT /ISAPI/AccessControl/FingerPrint/Delete",
    "REMOTE_CONTROL": "PUT /ISAPI/AccessControl/RemoteControl/door/<doorID>",
    "ACS_EVENT_SEARCH": "POST /ISAPI/AccessControl/AcsEvent",
    "ACS_WORK_STATUS": "GET /ISAPI/AccessControl/AcsWorkStatus",
    "PERMISSION_SET_UP": "PUT /ISAPI/AccessControl/Permission/SetUp",
}

# ─────────────────────────────────────────────────────────────
# FACE LIBRARY (FDLib) ENDPOINTS
# ─────────────────────────────────────────────────────────────
FACE_LIB = {
    "LIST": "GET /ISAPI/Intelligent/FDLib",
    "COUNT": "GET /ISAPI/Intelligent/FDLib/Count",
    "FACE_ADD": "POST /ISAPI/Intelligent/FDLib/FaceDataRecord",
    "FACE_SEARCH": "POST /ISAPI/Intelligent/FDLib/FDSearch",
    "FACE_DELETE": "PUT /ISAPI/Intelligent/FDLib/FDSearch/Delete",
    "FACE_PICTURE_UPLOAD": "POST /ISAPI/Intelligent/FDLib/pictureUpload",
}

# ─────────────────────────────────────────────────────────────
# STREAMING ENDPOINTS
# ─────────────────────────────────────────────────────────────
STREAMING = {
    "SNAPSHOT": "GET /ISAPI/Streaming/channels/<channelID>/picture",
}

# ─────────────────────────────────────────────────────────────
# COMMON ENUMS
# ─────────────────────────────────────────────────────────────

DOOR_CMD = {
    "OPEN": "open",
    "CLOSE": "close",
    "REMAIN_OPEN": "remain_open",
    "REMAIN_CLOSED": "remain_closed",
    "LOCK": "lock",
    "UNLOCK": "unlock",
}

CARD_TYPE = {
    "NORMAL": "normalCard",
    "VISITOR": "visitorCard",
    "BLACKLIST": "blackCard",
}

PERSON_TYPE = {
    "NORMAL": "normal",
    "VISITOR": "visitor",
    "BLACKLIST": "blackList",
}

# Major types for events
ACS_EVENT_MAJOR_TYPE = {
    "ALARM": 1,
    "EXCEPTION": 2,
    "OPERATION": 3,
    "INFO": 4,
    "OTHER": 5,
}

def parse_endpoint(entry: str):
    """Parsea una cadena tipo 'POST /ISAPI/...' en (metodo, path)."""
    parts = entry.strip().split()
    if len(parts) == 2:
        return parts[0], parts[1]
    return "GET", entry
