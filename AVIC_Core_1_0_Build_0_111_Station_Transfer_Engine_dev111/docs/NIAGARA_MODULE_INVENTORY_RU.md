# Niagara / IQVISION Module Inventory — supplied archive

## Статистика архива modules.zip

В архиве обнаружено 678 JAR entries:

| Suffix | Count | Architectural meaning used for AVIC design |
|---|---:|---|
| `-rt` | 420 | Runtime modules / station-side services and drivers |
| `-wb` | 143 | Workbench engineering tools and editors |
| `-ux` | 44 | User experience / client-side UI resources |
| `-doc` | 63 | Embedded documentation modules |
| `-se` | 7 | Security extensions |
| `baja.jar` | 1 | Core Baja framework artifact |

The archive includes modules for alarms, analytics, backup, BACnet, dashboards, control, converters, drivers, email, event, graphics (`gx`, `kitPx*`, `svg`, `pxEditor`), histories, hierarchy, tagging, schedules, Modbus TCP, MQTT, OPC/OPC UA, oBIX, SNMP, LDAP, SAML, mobile, reports, system monitoring, platform, provisioning, Point Database Manager, Trend N4, Trend graphics and many vendor-specific drivers.

Examples observed in the archive:
- Core/platform: `baja`, `platform`, `platDaemon`, `platDataRecovery`, `systemMonitor`, `systemDb`.
- Engineering: `control`, `kitControl`, `program`, `wiresheet`, `bajaui`, `pxEditor`, `gx`, `svg`.
- Operations: `alarm`, `event`, `history`, `schedule`, `email`, `onCall`, `sms`.
- Analytics and visualisation: `analytics`, `dashboard`, `chart`, `report`, `webChart`, `seriesTransform`.
- Drivers/integrations: `bacnet`, `modbusTcp`, `modbusAsync`, `TrendN4`, `opc`, `opcUaClient`, `opcUaServer`, `obix`, `snmp`, `abstractMqttDriver`.
- Security: `ldap`, `saml`, `electronicSignature`, `electronicSignatureRemote`, `tls`, `gauth`.
- Administration/recovery: `backup`, `cloudBackup`, `migration`, `provisioningNiagara`, `PointDatabaseManager`.

This is an inventory of archive filenames, not a reverse-engineered description of every JAR's internal behavior. No third-party binaries, licenses, certificates, keys or host-bound entitlements are included in AVIC.
