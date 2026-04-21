import requests
from requests.auth import HTTPDigestAuth

url = 'http://192.168.1.38:80/ISAPI/Event/notification/httpHosts'
auth = HTTPDigestAuth('admin', 'acc12345')

xml = '''<?xml version="1.0" encoding="UTF-8"?>
<HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<HttpHostNotification>
<id>1</id>
<url>http://192.168.1.10:8000/api/access/hikvision-webhook</url>
<protocolType>HTTP</protocolType>
<parameterFormatType>XML</parameterFormatType>
<addressingFormatType>ipaddress</addressingFormatType>
<ipAddress>192.168.1.10</ipAddress>
<portNo>8000</portNo>
</HttpHostNotification>
</HttpHostNotificationList>'''

r = requests.put(url, data=xml.encode('utf-8'), auth=auth, headers={'Content-Type': 'application/xml'}, timeout=10)
print(f'Status: {r.status_code}')
print(f'Response: {r.text[:500]}')