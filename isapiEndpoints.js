/**
 * ISAPI - Face Recognition Terminals (Value Series)
 * Hikvision ISAPI Reference — kaihome SRL / jcgonzalez.01@gmail.com
 *
 * Covered models (DS-K1A330, DS-K1T320*, DS-K1T321*, DS-K1T331,
 * DS-K1T341*, DS-K1T342*, DS-K1T343*, DS-K1T671, etc.)
 */

export const ISAPI_NS = {
  SYSTEM: "/ISAPI/System",
  SECURITY: "/ISAPI/Security",
  EVENT: "/ISAPI/Event/notification",
  ACCESS: "/ISAPI/AccessControl",
  FACE_LIB: "/ISAPI/Intelligent/FDLib",
  INTERCOM: "/ISAPI/VideoIntercom",
  SECURITY_CP: "/ISAPI/SecurityCP",
};

// ─────────────────────────────────────────────────────────────
// SYSTEM ENDPOINTS
// ─────────────────────────────────────────────────────────────
export const SYSTEM = {
  CAPABILITIES: "GET /ISAPI/System/capabilities",
  DEVICE_INFO: "GET /ISAPI/System/deviceInfo",
  ACTIVATE: "PUT /ISAPI/System/activate",
  FACTORY_RESET: "PUT /ISAPI/System/factoryReset",
  REBOOT: "PUT /ISAPI/System/reboot",
  TIME: "GET /ISAPI/System/time",
  NTP: "GET /ISAPI/System/time/ntp",
  NETWORK_CAPS: "GET /ISAPI/System/Network/capabilities",
};

// ─────────────────────────────────────────────────────────────
// SECURITY ENDPOINTS
// ─────────────────────────────────────────────────────────────
export const SECURITY = {
  CAPABILITIES: "GET /ISAPI/Security/capabilities",
  CHALLENGE: "POST /ISAPI/Security/challenge",
};

// ─────────────────────────────────────────────────────────────
// EVENT ENDPOINTS (Alert Stream & Webhooks)
// ─────────────────────────────────────────────────────────────
export const EVENT = {
  ALERT_STREAM: "GET /ISAPI/Event/notification/alertStream",
  HTTP_HOSTS: "GET /ISAPI/Event/notification/httpHosts",
  SET_HTTP_HOSTS: "PUT /ISAPI/Event/notification/httpHosts",
};

// ─────────────────────────────────────────────────────────────
// ACCESS CONTROL ENDPOINTS (Users, Cards, Events)
// ─────────────────────────────────────────────────────────────
export const ACCESS = {
  CAPABILITIES: "GET /ISAPI/AccessControl/capabilities",
  USER_COUNT: "GET /ISAPI/AccessControl/UserInfo/Count",
  USER_SEARCH: "POST /ISAPI/AccessControl/UserInfo/Search",
  USER_ADD: "POST /ISAPI/AccessControl/UserInfo/Record",
  USER_MODIFY: "PUT /ISAPI/AccessControl/UserInfo/Modify",
  USER_DELETE: "PUT /ISAPI/AccessControl/UserInfoDetail/Delete",
  ACS_EVENT: "POST /ISAPI/AccessControl/AcsEvent",
  REMOTE_OPEN: "PUT /ISAPI/AccessControl/RemoteControl/door/<doorID>",
};

// ─────────────────────────────────────────────────────────────
// FACE LIBRARY (FDLib) ENDPOINTS
// ─────────────────────────────────────────────────────────────
export const FACE_LIB = {
  FACE_ADD: "POST /ISAPI/Intelligent/FDLib/FaceDataRecord",
  FACE_SEARCH: "POST /ISAPI/Intelligent/FDLib/FDSearch",
  PICTURE_UPLOAD: "POST /ISAPI/Intelligent/FDLib/pictureUpload",
};

/**
 * Build a full URL with optional query parameters
 * @param {string} baseUrl - e.g. http://192.168.1.100
 * @param {string} path    - e.g. /ISAPI/System/deviceInfo
 * @param {boolean} json   - append ?format=json
 * @returns {string}
 */
export function buildUrl(baseUrl, path, json = true) {
  let url = `${baseUrl}${path}`;
  if (json) {
    url += path.includes("?") ? "&format=json" : "?format=json";
  }
  return url;
}

/**
 * Parse the method and path from a constant string like "POST /ISAPI/..."
 * @param {string} entry  - constant value e.g. ACCESS.USER_SEARCH
 * @returns {{ method: string, path: string }}
 */
export function parseEndpoint(entry) {
  const [method, path] = entry.trim().split(/\s+/);
  return { method, path };
}

// Export for CommonJS (Node.js)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    ISAPI_NS,
    SYSTEM,
    SECURITY,
    EVENT,
    ACCESS,
    FACE_LIB,
    buildUrl,
    parseEndpoint
  };
}
