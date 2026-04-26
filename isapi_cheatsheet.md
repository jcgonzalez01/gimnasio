# ISAPI — Face Recognition Terminals (Value Series)
# Quick Reference: Common Workflows
# KAIHOME S.R.L. | jcgonzalez.01@gmail.com
#
# Base: http(s)://<ip>:<port>
# Auth: HTTP Digest
# Format: append ?format=json to most endpoints

# ─────────────────────────────────────────────────
# 1. DEVICE BOOTSTRAP
# ─────────────────────────────────────────────────
GET  /ISAPI/System/capabilities          # check all supported features
GET  /ISAPI/System/deviceInfo            # model, firmware, serial
GET  /ISAPI/System/time                  # current time
PUT  /ISAPI/System/time                  # set time (manual mode)
GET  /ISAPI/AccessControl/capabilities   # access-specific caps

# ─────────────────────────────────────────────────
# 2. EVENT STREAMING (arming / alert stream)
# ─────────────────────────────────────────────────
# Option A: Long-poll stream (keep-alive)
GET  /ISAPI/Event/notification/alertStream
# Set Connection: keep-alive — events arrive as multipart/mixed chunks

# Option B: Subscription + HTTP push
GET  /ISAPI/Event/notification/subscribeEventCap    # check support
POST /ISAPI/Event/notification/subscribeEvent       # subscribe; returns subscribeEventID + heartbeat URL
PUT  /ISAPI/Event/notification/subscribeEvent/<id>  # update subscription
# Device posts events to your HTTP server (configure below)

# Configure your receiving server (listening host)
GET  /ISAPI/Event/notification/httpHosts/capabilities
PUT  /ISAPI/Event/notification/httpHosts             # set all hosts
PUT  /ISAPI/Event/notification/httpHosts/<hostID>    # set one host
POST /ISAPI/Event/notification/httpHosts             # add host

# ─────────────────────────────────────────────────
# 3. PERSON (USER) MANAGEMENT
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/UserInfo/capabilities     # check support + maxRecordNum
GET  /ISAPI/AccessControl/UserInfo/Count            # total persons in device
POST /ISAPI/AccessControl/UserInfo/Search           # search/list persons
POST /ISAPI/AccessControl/UserInfo/Record           # ADD new person
PUT  /ISAPI/AccessControl/UserInfo/SetUp            # APPLY (overwrite all)
PUT  /ISAPI/AccessControl/UserInfo/Modify           # EDIT person
PUT  /ISAPI/AccessControl/UserInfoDetail/Delete     # DELETE person
GET  /ISAPI/AccessControl/UserInfoDetail/DeleteProcess  # deletion progress

# Async import (for large batches - check isSupportBatchImport cap)
GET  /ISAPI/AccessControl/UserInfo/asyncImportDatasTasks/capabilities
GET  /ISAPI/AccessControl/UserInfo/asyncImportDatasTasks/status

# ─────────────────────────────────────────────────
# 4. CARD MANAGEMENT
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/CardInfo/capabilities     # check support
GET  /ISAPI/AccessControl/CardInfo/Count            # total cards
POST /ISAPI/AccessControl/CardInfo/Search           # search cards
POST /ISAPI/AccessControl/CardInfo/Record           # ADD card
PUT  /ISAPI/AccessControl/CardInfo/SetUp            # APPLY (overwrite all)
PUT  /ISAPI/AccessControl/CardInfo/Modify           # EDIT card
PUT  /ISAPI/AccessControl/CardInfo/Delete           # DELETE card(s)
GET  /ISAPI/AccessControl/CaptureCardInfo           # swipe card to collect No.

# ─────────────────────────────────────────────────
# 5. FINGERPRINT MANAGEMENT
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/FingerPrint/Count         # total FPs
POST /ISAPI/AccessControl/FingerPrintUpload         # search FPs (upload = query)
POST /ISAPI/AccessControl/FingerPrint/SetUp         # APPLY (overwrite)
POST /ISAPI/AccessControl/FingerPrintDownload       # ADD FP to device
GET  /ISAPI/AccessControl/FingerPrintProgress       # add progress
POST /ISAPI/AccessControl/FingerPrintModify         # EDIT FP
PUT  /ISAPI/AccessControl/FingerPrint/Delete        # DELETE FP
GET  /ISAPI/AccessControl/FingerPrint/DeleteProcess # delete progress
POST /ISAPI/AccessControl/CaptureFingerPrint        # live capture from reader

# ─────────────────────────────────────────────────
# 6. FACE PICTURE MANAGEMENT (in FDLib)
# ─────────────────────────────────────────────────
GET  /ISAPI/Intelligent/FDLib/capabilities
GET  /ISAPI/Intelligent/FDLib                       # list libraries
POST /ISAPI/Intelligent/FDLib                       # create library
GET  /ISAPI/Intelligent/FDLib/Count                 # total faces

POST /ISAPI/Intelligent/FDLib/FaceDataRecord        # ADD face (person + image)
PUT  /ISAPI/Intelligent/FDLib/FDSetUp               # APPLY (overwrite)
PUT  /ISAPI/Intelligent/FDLib/FDModify              # EDIT face
POST /ISAPI/Intelligent/FDLib/FDSearch              # SEARCH faces
PUT  /ISAPI/Intelligent/FDLib/FDSearch/Delete       # DELETE by search result
POST /ISAPI/Intelligent/FDLib/searchByPic           # search by picture comparison
POST /ISAPI/Intelligent/FDLib/pictureUpload         # upload picture to server

# Face capture (live) — returns binary face data
POST /ISAPI/AccessControl/CaptureFaceData
GET  /ISAPI/AccessControl/CaptureFaceData/Progress

# Face compare configuration
GET  /ISAPI/AccessControl/FaceCompareCond
PUT  /ISAPI/AccessControl/FaceCompareCond
GET  /ISAPI/AccessControl/FaceRecognizeMode
PUT  /ISAPI/AccessControl/FaceRecognizeMode

# ─────────────────────────────────────────────────
# 7. IRIS DATA MANAGEMENT
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/IrisInfo/capabilities
GET  /ISAPI/AccessControl/IrisInfo/count
POST /ISAPI/AccessControl/IrisInfo/search           # SEARCH
POST /ISAPI/AccessControl/IrisInfo/record           # ADD
PUT  /ISAPI/AccessControl/IrisInfo/setup            # APPLY (overwrite)
PUT  /ISAPI/AccessControl/IrisInfo/modify           # EDIT
PUT  /ISAPI/AccessControl/IrisInfo/delete           # DELETE
POST /ISAPI/AccessControl/captureIrisData           # live capture
GET  /ISAPI/AccessControl/captureIrisData/progress

# ─────────────────────────────────────────────────
# 8. DOOR / ACCESS POINT CONTROL
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/Door/param/<doorID>       # get door params
PUT  /ISAPI/AccessControl/Door/param/<doorID>       # set door params

# Remote control
GET  /ISAPI/AccessControl/RemoteControl/door/capabilities
PUT  /ISAPI/AccessControl/RemoteControl/door/<doorID>
# Body: { "RemoteControlDoor": { "cmd": "open" } }
# cmd options: open | close | remain_open | remain_closed | lock | unlock

# Door status / lock type
GET  /ISAPI/AccessControl/Configuration/lockType
PUT  /ISAPI/AccessControl/Configuration/lockType

# Magnetic contact definition
GET  /ISAPI/AccessControl/doorMagneticDefiniteRule

# ─────────────────────────────────────────────────
# 9. ACCESS LOG EVENTS (AcsEvent)
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/AcsEvent/capabilities
POST /ISAPI/AccessControl/AcsEvent              # search events by time/type/card
POST /ISAPI/AccessControl/AcsEventTotalNum      # count events matching filter
GET  /ISAPI/AccessControl/AcsWorkStatus         # device work status
# Event storage config
GET  /ISAPI/AccessControl/AcsEvent/StorageCfg
PUT  /ISAPI/AccessControl/AcsEvent/StorageCfg

# ─────────────────────────────────────────────────
# 10. GENERAL ACCESS CONFIG (AcsCfg)
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/AcsCfg/capabilities
GET  /ISAPI/AccessControl/AcsCfg
PUT  /ISAPI/AccessControl/AcsCfg
# Contains: verifyMode, faceCompareSecurity, maskDetect, openDoorCondition...

# ─────────────────────────────────────────────────
# 11. SCHEDULE / PERMISSION PLANS
# ─────────────────────────────────────────────────
# Verify plan template (auth schedule for card reader)
GET|PUT /ISAPI/AccessControl/VerifyPlanTemplate/<templateNo>
GET|PUT /ISAPI/AccessControl/VerifyWeekPlanCfg/<templateNo>
GET|PUT /ISAPI/AccessControl/VerifyHolidayGroupCfg/<groupNo>
GET|PUT /ISAPI/AccessControl/VerifyHolidayPlanCfg/<templateNo>

# User right plan (when person can access)
GET|PUT /ISAPI/AccessControl/UserRightPlanTemplate/<templateNo>
GET|PUT /ISAPI/AccessControl/UserRightWeekPlanCfg/<templateNo>
GET|PUT /ISAPI/AccessControl/UserRightHolidayGroupCfg/<groupNo>
GET|PUT /ISAPI/AccessControl/UserRightHolidayPlanCfg/<templateNo>

# Door status plan (when door auto-opens/closes)
GET|PUT /ISAPI/AccessControl/DoorStatusPlan/<planID>
GET|PUT /ISAPI/AccessControl/DoorStatusPlanTemplate/<templateNo>
GET|PUT /ISAPI/AccessControl/DoorStatusWeekPlanCfg/<templateNo>
GET|PUT /ISAPI/AccessControl/DoorStatusHolidayGroupCfg/<groupNo>
GET|PUT /ISAPI/AccessControl/DoorStatusHolidayPlanCfg/<templateNo>

# ─────────────────────────────────────────────────
# 12. ANTI-PASSBACK
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/AntiSneakCfg
PUT  /ISAPI/AccessControl/AntiSneakCfg
PUT  /ISAPI/AccessControl/ClearAntiSneak             # clear APB records
GET  /ISAPI/AccessControl/AntiPassback/resetRules
PUT  /ISAPI/AccessControl/AntiPassback/resetRules

# Per card reader
GET  /ISAPI/AccessControl/CardReaderAntiSneakCfg/<cardReaderID>
PUT  /ISAPI/AccessControl/CardReaderAntiSneakCfg/<cardReaderID>

# ─────────────────────────────────────────────────
# 13. EVENT-CARD LINKAGE
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/EventCardLinkageCfg/capabilities
POST /ISAPI/AccessControl/EventCardLinkageCfg/search
GET  /ISAPI/AccessControl/EventCardLinkageCfg/<linkageID>
PUT  /ISAPI/AccessControl/EventCardLinkageCfg/<linkageID>
PUT  /ISAPI/AccessControl/EventCardLinkageCfgDelete
GET  /ISAPI/AccessControl/EventCardNoList            # list of card IDs in linkage
PUT  /ISAPI/AccessControl/EventOptimizationCfg       # merge/optimize events

# ─────────────────────────────────────────────────
# 14. QR CODE
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/QRCodeEncryption/capabilities
PUT  /ISAPI/AccessControl/QRCodeEncryption
POST /ISAPI/AccessControl/QRCodeInfo                # generate QR code by device
POST /ISAPI/AccessControl/QRCodeEvent               # QR event search

# ─────────────────────────────────────────────────
# 15. MULTI-FACTOR / GROUP AUTH
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/MultiCardCfg/capabilities
GET  /ISAPI/AccessControl/MultiCardCfg/<cardNo>
PUT  /ISAPI/AccessControl/MultiCardCfg/<cardNo>
GET  /ISAPI/AccessControl/GroupCfg/<groupID>
PUT  /ISAPI/AccessControl/GroupCfg/<groupID>
PUT  /ISAPI/AccessControl/ClearGroupCfg

# ─────────────────────────────────────────────────
# 16. CARD READER CONFIG
# ─────────────────────────────────────────────────
GET  /ISAPI/AccessControl/CardReaderCfg/<cardReaderID>
PUT  /ISAPI/AccessControl/CardReaderCfg/<cardReaderID>
GET  /ISAPI/AccessControl/CardReaderPlan/<cardReaderID>
PUT  /ISAPI/AccessControl/CardReaderPlan/<cardReaderID>
GET  /ISAPI/AccessControl/CardVerificationRule
PUT  /ISAPI/AccessControl/CardVerificationRule

# ─────────────────────────────────────────────────
# 17. NTP / TIME SYNC
# ─────────────────────────────────────────────────
GET  /ISAPI/System/time/capabilities
PUT  /ISAPI/System/time                             # set time / mode
PUT  /ISAPI/System/time/ntpServers                  # set NTP server
PUT  /ISAPI/System/time/timeZone                    # set timezone
PUT  /ISAPI/System/time/ntp                         # NTP server mode
PUT  /ISAPI/System/time/NTPService                  # NTP service params

# ─────────────────────────────────────────────────
# 18. FIRMWARE UPGRADE
# ─────────────────────────────────────────────────
# Standard upgrade
POST /ISAPI/System/updateFirmware                   # upload firmware binary
GET  /ISAPI/System/upgradeStatus                    # poll progress
PUT  /ISAPI/System/reboot                           # reboot after upgrade

# Online upgrade
GET  /ISAPI/System/firmwareCodeV2                   # get firmware ID
POST /ISAPI/System/onlineUpgrade/task               # create upgrade task
PUT  /ISAPI/System/onlineUpgrade/upgrade            # apply task
GET  /ISAPI/System/onlineUpgrade/status             # poll progress
PUT  /ISAPI/System/onlineUpgrade/CancelUpgrade      # cancel

# Peripheral upgrade (card readers, locks)
GET  /ISAPI/System/AcsUpdate/capabilities
# POST /ISAPI/System/updateFirmware?type=<type>&moduleAddress=<addr>

# ─────────────────────────────────────────────────
# 19. VIDEO INTERCOM
# ─────────────────────────────────────────────────
GET  /ISAPI/VideoIntercom/deviceId
PUT  /ISAPI/VideoIntercom/callSignal                # initiate/answer call
GET  /ISAPI/VideoIntercom/callStatus
GET  /ISAPI/VideoIntercom/callerInfo
PUT  /ISAPI/VideoIntercom/Elevators/<elevatorID>
GET  /ISAPI/VideoIntercom/SmartLock/lockParam

# ─────────────────────────────────────────────────
# 20. TWO-WAY AUDIO
# ─────────────────────────────────────────────────
GET  /ISAPI/System/TwoWayAudio/channels
PUT  /ISAPI/System/TwoWayAudio/channels/<audioID>/open
GET  /ISAPI/System/TwoWayAudio/channels/1/audioData   # receive audio (binary)
PUT  /ISAPI/System/TwoWayAudio/channels/1/audioData   # send audio (binary)
PUT  /ISAPI/System/TwoWayAudio/channels/<audioID>/close

# ─────────────────────────────────────────────────
# COMMON NOTES
# ─────────────────────────────────────────────────
# 1. Always GET /ISAPI/AccessControl/capabilities first to check feature support
# 2. Most endpoints support both XML and JSON (?format=json)
# 3. Digest auth — use proper nonce handling
# 4. SetUp = overwrite all  |  Record/Modify = add/edit individually
# 5. For biometrics > 1000 records use async import tasks
# 6. maxRecordNum per batch is returned by capabilities endpoint
# 7. Events from alertStream arrive as multipart/mixed; parse boundary carefully
# 8. heartBeat eventType = keepalive ping on subscription stream
