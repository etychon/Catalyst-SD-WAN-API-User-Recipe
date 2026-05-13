# Device Health, Interface, and Cellular Field Dictionary

This dictionary explains the fields shown in a Cisco Catalyst SD-WAN Manager JSON payload that combines device health, interface inventory/statistics, and enriched cellular radio data.

Field names are kept exactly as they appear in the API response. Relationships use clickable internal references so this file can be used by humans and as LLM context.

## Reading Notes

- Time fields such as [`lastupdated`](#lastupdated) and [`uptime-date`](#uptime-date) are Unix epoch timestamps in milliseconds unless your deployment documents otherwise.
- Values such as `0.0.0.0`, `N/A`, `None`, and `0` may mean "not assigned", "not applicable", or "not currently reported". Treat them as unknown or unavailable unless the specific field definition says otherwise.
- Hyphenated and camelCase names can describe the same concept across different APIs. For example, [`system-ip`](#system-ip), [`local-system-ip`](#local-system-ip), [`deviceId`](#deviceid), [`vdevice-name`](#vdevice-name), and [`vdevice-dataKey`](#vdevice-datakey) are all part of the device identity model.

## Top-Level Device Fields

| Field | Meaning | Related fields |
| --- | --- | --- |
| <a id="bfdsessions"></a>`bfdSessions` | Human-readable BFD tunnel session summary. In the example, `0 (6)` means 0 sessions up out of 6 total or expected sessions, depending on the source endpoint formatting. | Compare with numeric [`bfdSessionsUp`](#bfdsessionsup). Related to tunnel/interface state in [`deviceInterface`](#deviceinterface). |
| <a id="bfdsessionsup"></a>`bfdSessionsUp` | Numeric count of BFD sessions currently up. More useful for calculations than [`bfdSessions`](#bfdsessions). | Use with [`bfdSessions`](#bfdsessions) to compute tunnel health. |
| <a id="board-serial"></a>`board-serial` | Hardware board serial number reported by the device. | Related to chassis identity fields [`uuid`](#uuid), [`device-model`](#device-model), and [`model_sku`](#model_sku). |
| <a id="certificate-validity"></a>`certificate-validity` | Certificate status as interpreted by SD-WAN Manager, for example `Valid`. | Related to [`validity`](#validity) and control-plane reachability fields such as [`controlConnections`](#controlconnections). |
| <a id="connectedvmanages"></a>`connectedVManages` | List of SD-WAN Manager system IPs or addresses this device is connected to. | Related to [`controlConnections`](#controlconnections), [`max-controllers`](#max-controllers), and [`reachability`](#reachability). |
| <a id="controlconnections"></a>`controlConnections` | Number of active control connections from the device to SD-WAN controllers/managers. | Related to [`connectedVManages`](#connectedvmanages), [`certificate-validity`](#certificate-validity), and [`state_description`](#state_description). |
| <a id="device-groups"></a>`device-groups` | List of SD-WAN Manager device groups assigned to the device. | Related to organizational fields [`site-id`](#site-id), [`site-name`](#site-name), and RBAC/dashboard scoping. |
| <a id="device-model"></a>`device-model` | Platform model name, for example `vedge-IR-1101`. | Related to [`model_sku`](#model_sku), [`platform`](#platform), [`personality`](#personality), and [`device-type`](#device-type). |
| <a id="device-type"></a>`device-type` | SD-WAN device family or role, for example `vedge`. | Related to [`personality`](#personality) and [`device-model`](#device-model). |
| <a id="deviceid"></a>`deviceId` | Device identifier used by some SD-WAN Manager APIs. In this payload it matches the device system IP. | Related to [`system-ip`](#system-ip), [`local-system-ip`](#local-system-ip), and [`vdevice-name`](#vdevice-name). |
| <a id="deviceinterface"></a>`deviceInterface` | Array of interface records for the device. Each object describes one interface, its state, addressing, counters, and speed. | See [Interface Fields](#interface-fields). |
| <a id="domain-id"></a>`domain-id` | SD-WAN domain identifier. Often used in multi-domain or hierarchical deployments. | Related to [`site-id`](#site-id) and topology grouping. |
| <a id="health"></a>`health` | High-level health color or status calculated by SD-WAN Manager, for example `red`. | Compare with [`state`](#state), [`status`](#status), [`statusOrder`](#statusorder), and [`state_description`](#state_description). |
| <a id="host-name"></a>`host-name` | Device hostname. | Related to [`vdevice-host-name`](#vdevice-host-name), [`deviceId`](#deviceid), and [`system-ip`](#system-ip). |
| <a id="isdevicegeodata"></a>`isDeviceGeoData` | Boolean indicating whether device-specific geographic data is available or trusted from SD-WAN Manager. | Related to [`latitude`](#latitude), [`longitude`](#longitude), and [`site-name`](#site-name). |
| <a id="lastupdated"></a>`lastupdated` | Last time the record was updated, usually Unix epoch milliseconds. Appears at top level and inside nested interface/cellular records. | Related to [`uptime-date`](#uptime-date) and every nested record timestamp. |
| <a id="latitude"></a>`latitude` | Device or site latitude as a string. | Related to [`longitude`](#longitude), [`isDeviceGeoData`](#isdevicegeodata), and [`site-name`](#site-name). |
| <a id="layoutlevel"></a>`layoutLevel` | Topology layout depth or hierarchy level used by SD-WAN Manager UI/topology views. | Related to [`site-id`](#site-id), [`site-name`](#site-name), and map/topology rendering. |
| <a id="linux_cpu_count"></a>`linux_cpu_count` | Number of CPU cores visible to the Linux layer of the device. | Related to [`total_cpu_count`](#total_cpu_count), [`platform`](#platform), and capacity/health views. |
| <a id="local-system-ip"></a>`local-system-ip` | Local SD-WAN system IP of the device. | Usually the same as [`system-ip`](#system-ip) and [`deviceId`](#deviceid). |
| <a id="longitude"></a>`longitude` | Device or site longitude as a string. | Related to [`latitude`](#latitude), [`isDeviceGeoData`](#isdevicegeodata), and topology maps. |
| <a id="max-controllers"></a>`max-controllers` | Maximum or configured controller connection count reported for this device context. A value of `0` may mean unavailable in this payload. | Compare with actual [`controlConnections`](#controlconnections). |
| <a id="model_sku"></a>`model_sku` | Model SKU or ordering SKU when known. `None` means the value was not available. | Related to [`device-model`](#device-model) and [`board-serial`](#board-serial). |
| <a id="omppeers"></a>`ompPeers` | Number of OMP peers reported by the device. OMP peers indicate overlay routing/control-plane adjacency. | Related to [`controlConnections`](#controlconnections) and [`state_description`](#state_description). |
| <a id="personality"></a>`personality` | SD-WAN software personality or role, for example `vedge`. | Related to [`device-type`](#device-type) and [`device-model`](#device-model). |
| <a id="platform"></a>`platform` | CPU architecture or platform string, for example `aarch64`. | Related to [`device-model`](#device-model), [`linux_cpu_count`](#linux_cpu_count), and [`total_cpu_count`](#total_cpu_count). |
| <a id="reachability"></a>`reachability` | Whether SD-WAN Manager can currently reach the device, for example `reachable`. | Related to [`controlConnections`](#controlconnections), [`health`](#health), and [`status`](#status). |
| <a id="site-id"></a>`site-id` | SD-WAN site identifier. Used to group devices by location or logical site. | Related to [`site-name`](#site-name), [`latitude`](#latitude), and [`longitude`](#longitude). |
| <a id="site-name"></a>`site-name` | Human-readable site name. | Related to [`site-id`](#site-id) and map/topology fields. |
| <a id="state"></a>`state` | Device state color, for example `green`. This may differ from [`health`](#health) depending on the endpoint and calculation model. | Compare with [`health`](#health), [`status`](#status), and [`state_description`](#state_description). |
| <a id="state_description"></a>`state_description` | Human-readable state reason, for example `All daemons up`. | Explains [`state`](#state) and helps interpret [`health`](#health). |
| <a id="status"></a>`status` | High-level status string, for example `normal`. | Related to [`statusOrder`](#statusorder), [`state`](#state), and [`health`](#health). |
| <a id="statusorder"></a>`statusOrder` | Numeric sort/ranking value for status. Useful for dashboard ordering. | Related to [`status`](#status) and [`health`](#health). |
| <a id="system-ip"></a>`system-ip` | SD-WAN system IP, the primary stable overlay identifier for a device. | Related to [`deviceId`](#deviceid), [`local-system-ip`](#local-system-ip), [`vdevice-name`](#vdevice-name), and [`Sdwan-system-intf`](#sdwan-system-intf-note). |
| <a id="terraenrichedfromsync"></a>`terraEnrichedFromSync` | Enriched nested data joined from synchronized data services. In this example it contains cellular radio records. | See [`cellular_dataservice`](#cellular_dataservice) and [Cellular Radio Fields](#cellular-radio-fields). |
| <a id="testbed_mode"></a>`testbed_mode` | Boolean flag indicating whether the device or manager context is marked as testbed/lab mode. | Use with environment classification and dashboard filtering. |
| <a id="timezone"></a>`timezone` | Device timezone string. | Related to timestamp display for [`lastupdated`](#lastupdated) and [`uptime-date`](#uptime-date). |
| <a id="total_cpu_count"></a>`total_cpu_count` | Total CPU count reported for the device context. | Compare with [`linux_cpu_count`](#linux_cpu_count). |
| <a id="uptime-date"></a>`uptime-date` | Device boot or uptime reference timestamp, usually Unix epoch milliseconds. | Related to [`lastupdated`](#lastupdated). |
| <a id="uuid"></a>`uuid` | Unique device identifier. In the example it includes the product PID and serial-like value. | Related to [`board-serial`](#board-serial), [`deviceId`](#deviceid), and [`system-ip`](#system-ip). |
| <a id="validity"></a>`validity` | Certificate or device validity state, for example `valid`. | Related to [`certificate-validity`](#certificate-validity). |
| <a id="version"></a>`version` | Software version running on the device. | Related to compatibility, API interpretation, and field availability. |

## Interface Fields

These fields appear inside each object in [`deviceInterface`](#deviceinterface).

| Field | Meaning | Related fields |
| --- | --- | --- |
| <a id="auto-downstream-bandwidth"></a>`auto-downstream-bandwidth` | Automatically detected or configured downstream bandwidth. `N/A` means unavailable or not applicable. | Related to [`bw-down-util`](#bw-down-util) and [`speed-mbps`](#speed-mbps). |
| <a id="auto-negotiate"></a>`auto-negotiate` | Whether Ethernet auto-negotiation is enabled on the interface. | Related to [`negotiated-duplex-mode`](#negotiated-duplex-mode), [`negotiated-port-speed`](#negotiated-port-speed), and [`speed-mbps`](#speed-mbps). |
| <a id="auto-upstream-bandwidth"></a>`auto-upstream-bandwidth` | Automatically detected or configured upstream bandwidth. `N/A` means unavailable or not applicable. | Related to [`bw-up-util`](#bw-up-util) and [`speed-mbps`](#speed-mbps). |
| <a id="bia-address"></a>`bia-address` | Burned-in hardware MAC address. | Compare with current [`hwaddr`](#hwaddr). |
| <a id="bw-down-util"></a>`bw-down-util` | Downstream bandwidth utilization percentage or formatted numeric string. | Related to [`rx-kbps`](#rx-kbps), [`speed-mbps`](#speed-mbps), and [`auto-downstream-bandwidth`](#auto-downstream-bandwidth). |
| <a id="bw-up-util"></a>`bw-up-util` | Upstream bandwidth utilization percentage or formatted numeric string. | Related to [`tx-kbps`](#tx-kbps), [`speed-mbps`](#speed-mbps), and [`auto-upstream-bandwidth`](#auto-upstream-bandwidth). |
| <a id="fec-mode"></a>`fec-mode` | Whether Forward Error Correction is enabled for the interface or tunnel context. | Related to tunnel quality and [`Tunnel0`](#tunnel0-note) records. |
| <a id="hwaddr"></a>`hwaddr` | Current hardware/MAC address. | Compare with [`bia-address`](#bia-address). |
| <a id="if-admin-status"></a>`if-admin-status` | Configured administrative state, for example `if-state-up` or `if-state-down`. | Compare with operational state [`if-oper-status`](#if-oper-status). |
| <a id="if-oper-status"></a>`if-oper-status` | Actual operational state, for example `if-oper-state-ready`, `if-oper-state-lower-layer-down`, or `if-oper-state-no-pass`. | Interpret together with [`if-admin-status`](#if-admin-status), counters, and physical status. |
| <a id="ifindex"></a>`ifindex` | Numeric interface index assigned by the device. | Related to [`ifname`](#ifname) and SNMP/interface correlation. |
| <a id="ifname"></a>`ifname` | Interface name, for example `GigabitEthernet0/0/0`, `Cellular0/1/0`, `Tunnel0`, or `Loopback65529`. | Related to [`interface-type`](#interface-type), [`vpn-id`](#vpn-id), and [`vdevice-dataKey`](#vdevice-datakey). |
| <a id="interface-type"></a>`interface-type` | IANA interface type string, for example Ethernet, tunnel, loopback, serial, or virtual. | Related to [`ifname`](#ifname) and dashboard grouping. |
| <a id="ip-address"></a>`ip-address` | IPv4 address assigned to the interface. `0.0.0.0` usually means no IPv4 address assigned or not applicable. | Related to [`ipv4-subnet-mask`](#ipv4-subnet-mask), [`vpn-id`](#vpn-id), and [`vdevice-dataKey`](#vdevice-datakey). |
| <a id="ipv4-subnet-mask"></a>`ipv4-subnet-mask` | IPv4 subnet mask for [`ip-address`](#ip-address). | Related to [`ip-address`](#ip-address). |
| <a id="ipv4-tcp-adjust-mss"></a>`ipv4-tcp-adjust-mss` | IPv4 TCP MSS adjustment configured on the interface. `0` usually means not configured. | Related to MTU tuning via [`mtu`](#mtu). |
| <a id="ipv6-addrs"></a>`ipv6-addrs` | IPv6 address or addresses assigned to the interface. | Related to [`ipv6-tcp-adjust-mss`](#ipv6-tcp-adjust-mss). |
| <a id="ipv6-tcp-adjust-mss"></a>`ipv6-tcp-adjust-mss` | IPv6 TCP MSS adjustment configured on the interface. `0` usually means not configured. | Related to [`mtu`](#mtu). |
| <a id="mtu"></a>`mtu` | Interface Maximum Transmission Unit. | Related to MSS fields [`ipv4-tcp-adjust-mss`](#ipv4-tcp-adjust-mss) and [`ipv6-tcp-adjust-mss`](#ipv6-tcp-adjust-mss). |
| <a id="negotiated-duplex-mode"></a>`negotiated-duplex-mode` | Ethernet duplex mode negotiated or configured, for example `full-duplex` or `auto-duplex`. | Related to [`auto-negotiate`](#auto-negotiate) and [`negotiated-port-speed`](#negotiated-port-speed). |
| <a id="negotiated-port-speed"></a>`negotiated-port-speed` | Ethernet port speed negotiated or configured, for example `speed-100mb` or `speed-1gb`. | Compare with numeric [`speed-mbps`](#speed-mbps). |
| <a id="num-flaps"></a>`num-flaps` | Number of interface state flaps observed. | Related to [`if-oper-status`](#if-oper-status) and operational stability alerts. |
| <a id="rx-drops"></a>`rx-drops` | Received packets dropped. | Related to [`rx-errors`](#rx-errors), [`rx-packets`](#rx-packets), and interface congestion/quality. |
| <a id="rx-errors"></a>`rx-errors` | Receive-side error count. | Related to [`rx-drops`](#rx-drops), [`rx-packets`](#rx-packets), and physical/link health. |
| <a id="rx-kbps"></a>`rx-kbps` | Receive throughput in kilobits per second. | Related to [`bw-down-util`](#bw-down-util), [`rx-octets`](#rx-octets), and [`speed-mbps`](#speed-mbps). |
| <a id="rx-octets"></a>`rx-octets` | Total received octets/bytes counter. | Related to [`rx-kbps`](#rx-kbps) and [`rx-packets`](#rx-packets). |
| <a id="rx-packets"></a>`rx-packets` | Total received packet counter. | Related to [`rx-pps`](#rx-pps), [`rx-errors`](#rx-errors), and [`rx-drops`](#rx-drops). |
| <a id="rx-pps"></a>`rx-pps` | Receive packets per second. | Related to [`rx-packets`](#rx-packets) and [`rx-kbps`](#rx-kbps). |
| <a id="speed-mbps"></a>`speed-mbps` | Interface speed in megabits per second. | Used with [`rx-kbps`](#rx-kbps), [`tx-kbps`](#tx-kbps), [`bw-down-util`](#bw-down-util), and [`bw-up-util`](#bw-up-util). |
| <a id="tx-drops"></a>`tx-drops` | Transmitted packets dropped. | Related to [`tx-errors`](#tx-errors), [`tx-packets`](#tx-packets), and congestion. |
| <a id="tx-errors"></a>`tx-errors` | Transmit-side error count. | Related to [`tx-drops`](#tx-drops) and [`tx-packets`](#tx-packets). |
| <a id="tx-kbps"></a>`tx-kbps` | Transmit throughput in kilobits per second. | Related to [`bw-up-util`](#bw-up-util), [`tx-octets`](#tx-octets), and [`speed-mbps`](#speed-mbps). |
| <a id="tx-octets"></a>`tx-octets` | Total transmitted octets/bytes counter. | Related to [`tx-kbps`](#tx-kbps) and [`tx-packets`](#tx-packets). |
| <a id="tx-packets"></a>`tx-packets` | Total transmitted packet counter. | Related to [`tx-pps`](#tx-pps), [`tx-errors`](#tx-errors), and [`tx-drops`](#tx-drops). |
| <a id="tx-pps"></a>`tx-pps` | Transmit packets per second. | Related to [`tx-packets`](#tx-packets) and [`tx-kbps`](#tx-kbps). |
| <a id="vdevice-datakey"></a>`vdevice-dataKey` | Composite key created by SD-WAN Manager to uniquely identify the interface record. In the example it combines system IP, VPN ID, interface name, IP address, and MAC address. | Related to [`system-ip`](#system-ip), [`vpn-id`](#vpn-id), [`ifname`](#ifname), [`ip-address`](#ip-address), and [`hwaddr`](#hwaddr). |
| <a id="vdevice-host-name"></a>`vdevice-host-name` | Hostname copied into the nested interface or cellular record. | Related to top-level [`host-name`](#host-name). |
| <a id="vdevice-name"></a>`vdevice-name` | Device name copied into the nested record. Often the system IP. | Related to [`system-ip`](#system-ip) and [`deviceId`](#deviceid). |
| <a id="vpn-id"></a>`vpn-id` | SD-WAN VPN/VRF identifier where the interface exists. VPN 0 is commonly transport; service VPNs and special/system VPNs may use other IDs. | Related to [`ifname`](#ifname), [`ip-address`](#ip-address), and [`vdevice-dataKey`](#vdevice-datakey). |

## Interface Name Notes

| Interface pattern | Meaning |
| --- | --- |
| <a id="cellular-interface-note"></a>`Cellular...` | Cellular WAN interface. Cross-reference with [`cellular-interface`](#cellular-interface) in radio records. |
| <a id="tunnel0-note"></a>`Tunnel0` | Overlay tunnel interface. Correlate with [`bfdSessions`](#bfdsessions), [`bfdSessionsUp`](#bfdsessionsup), and tunnel SLA metrics. |
| <a id="sdwan-system-intf-note"></a>`Sdwan-system-intf` | SD-WAN system interface carrying the device [`system-ip`](#system-ip). |
| `Loopback...` | Loopback interface, often used for system, management, or internal addressing depending on platform. |
| `FastEthernet...` / `GigabitEthernet...` | Physical Ethernet interfaces. Use speed, duplex, admin/oper status, and counters for monitoring. |
| `Vlan...` | Switched virtual interface. Use with site/LAN or platform-specific switching views. |

## Cellular Enrichment Fields

These fields appear under [`terraEnrichedFromSync`](#terraenrichedfromsync).

| Field | Meaning | Related fields |
| --- | --- | --- |
| <a id="cellular_dataservice"></a>`cellular_dataservice` | Container for cellular records synchronized from cellular data services. | Contains [`cellular_sync_device_cellular_radio`](#cellular_sync_device_cellular_radio). |
| <a id="cellular_sync_device_cellular_radio"></a>`cellular_sync_device_cellular_radio` | Array of cellular radio records, one per reported cellular interface/radio technology combination. | See [Cellular Radio Fields](#cellular-radio-fields). |

## Cellular Radio Fields

These fields appear inside each object in [`cellular_sync_device_cellular_radio`](#cellular_sync_device_cellular_radio).

| Field | Meaning | Related fields |
| --- | --- | --- |
| <a id="bandwidth"></a>`bandwidth` | LTE channel bandwidth, for example `bandwidth-20-mhz`. | Related to [`radio-band`](#radio-band), [`radio-rx-channel`](#radio-rx-channel), and [`radio-tx-channel`](#radio-tx-channel). |
| <a id="cellular-interface"></a>`cellular-interface` | Cellular interface name for the radio record. | Join to interface [`ifname`](#ifname), especially records matching `Cellular...`. |
| <a id="nr5g-band"></a>`nr5g-band` | 5G NR band. `0` can mean no active 5G NR value reported. | Related to [`nr5g-rsrp`](#nr5g-rsrp), [`nr5g-rsrq`](#nr5g-rsrq), and [`nr5g-snr`](#nr5g-snr). |
| <a id="nr5g-bw"></a>`nr5g-bw` | 5G NR bandwidth. `nr5g-bw-unknown` means not known or not active. | Related to [`nr5g-band`](#nr5g-band). |
| <a id="nr5g-pci"></a>`nr5g-pci` | 5G NR Physical Cell ID. | Related to [`pci`](#pci) for LTE. |
| <a id="nr5g-rsrp"></a>`nr5g-rsrp` | 5G Reference Signal Received Power. Measures signal strength in dBm when active. | LTE equivalent: [`radio-rsrp`](#radio-rsrp). |
| <a id="nr5g-rsrq"></a>`nr5g-rsrq` | 5G Reference Signal Received Quality. Measures signal quality. | LTE equivalent: [`radio-rsrq`](#radio-rsrq). |
| <a id="nr5g-rssi"></a>`nr5g-rssi` | 5G Received Signal Strength Indicator. | LTE equivalent: [`radio-rssi`](#radio-rssi). |
| <a id="nr5g-rxch"></a>`nr5g-rxch` | 5G receive channel number. | Related to [`nr5g-txch`](#nr5g-txch). |
| <a id="nr5g-snr"></a>`nr5g-snr` | 5G signal-to-noise ratio. Higher is generally better. | LTE equivalent: [`radio-snr`](#radio-snr). |
| <a id="nr5g-txch"></a>`nr5g-txch` | 5G transmit channel number. | Related to [`nr5g-rxch`](#nr5g-rxch). |
| <a id="pci"></a>`pci` | LTE Physical Cell ID. Identifies the serving LTE cell sector. | 5G equivalent: [`nr5g-pci`](#nr5g-pci). |
| <a id="radio-band"></a>`radio-band` | LTE radio band. | Related to [`bandwidth`](#bandwidth) and RF planning. |
| <a id="radio-power-mode"></a>`radio-power-mode` | Radio power state, for example `radio-power-mode-online`. | Related to interface operational status [`if-oper-status`](#if-oper-status). |
| <a id="radio-rat-preference"></a>`radio-rat-preference` | Preferred Radio Access Technology selection policy, for example automatic LTE selection. | Related to actual selected technology [`radio-rat-selected`](#radio-rat-selected). |
| <a id="radio-rat-selected"></a>`radio-rat-selected` | Currently selected Radio Access Technology, for example `4G`. | Related to [`radio-rat-preference`](#radio-rat-preference) and 5G fields such as [`nr5g-band`](#nr5g-band). |
| <a id="radio-rsrp"></a>`radio-rsrp` | LTE Reference Signal Received Power in dBm. This is a key signal strength metric; less negative is better. | Use with [`radio-rsrq`](#radio-rsrq), [`radio-rssi`](#radio-rssi), and [`radio-snr`](#radio-snr). |
| <a id="radio-rsrq"></a>`radio-rsrq` | LTE Reference Signal Received Quality in dB. Less negative is usually better. | Use with [`radio-rsrp`](#radio-rsrp) and [`radio-snr`](#radio-snr). |
| <a id="radio-rssi"></a>`radio-rssi` | LTE Received Signal Strength Indicator in dBm. Measures total received power, including signal and noise. | Use with [`radio-rsrp`](#radio-rsrp) and [`radio-snr`](#radio-snr). |
| <a id="radio-rx-channel"></a>`radio-rx-channel` | LTE receive channel number. | Related to [`radio-tx-channel`](#radio-tx-channel), [`radio-band`](#radio-band), and carrier planning. |
| <a id="radio-snr"></a>`radio-snr` | LTE signal-to-noise ratio in dB. Higher is generally better. | Use with [`radio-rsrp`](#radio-rsrp) and [`radio-rsrq`](#radio-rsrq) for cellular quality classification. |
| <a id="radio-tx-channel"></a>`radio-tx-channel` | LTE transmit channel number. A value such as `65535` can indicate unavailable, unknown, or platform-specific reporting. | Related to [`radio-rx-channel`](#radio-rx-channel). |

## Important Relationships

| Relationship | How to use it |
| --- | --- |
| Device identity | Use [`system-ip`](#system-ip) as the primary overlay key. Join with [`deviceId`](#deviceid), [`local-system-ip`](#local-system-ip), [`vdevice-name`](#vdevice-name), and nested [`vdevice-dataKey`](#vdevice-datakey). |
| Interface identity | A unique interface row can be built from [`system-ip`](#system-ip), [`vpn-id`](#vpn-id), [`ifname`](#ifname), [`ip-address`](#ip-address), and [`hwaddr`](#hwaddr), which are embedded in [`vdevice-dataKey`](#vdevice-datakey). |
| Admin versus operational state | [`if-admin-status`](#if-admin-status) is the configured state; [`if-oper-status`](#if-oper-status) is what is actually happening. A dashboard should show both. |
| Throughput and utilization | [`rx-kbps`](#rx-kbps) and [`tx-kbps`](#tx-kbps) are current traffic rates; [`bw-down-util`](#bw-down-util) and [`bw-up-util`](#bw-up-util) are utilization views based on configured or detected bandwidth and [`speed-mbps`](#speed-mbps). |
| Packet quality | Use [`rx-errors`](#rx-errors), [`tx-errors`](#tx-errors), [`rx-drops`](#rx-drops), [`tx-drops`](#tx-drops), and [`num-flaps`](#num-flaps) to detect link degradation even when an interface is up. |
| Tunnel health | Use [`bfdSessionsUp`](#bfdsessionsup) and [`bfdSessions`](#bfdsessions) with tunnel/interface records such as [`Tunnel0`](#tunnel0-note). For detailed tunnel SLA, join with app-route latency/loss/jitter statistics. |
| Cellular interface to radio | Join interface [`ifname`](#ifname) values such as `Cellular0/1/0` to cellular radio [`cellular-interface`](#cellular-interface). |
| Cellular quality | Classify signal using [`radio-rsrp`](#radio-rsrp), [`radio-rsrq`](#radio-rsrq), [`radio-rssi`](#radio-rssi), and [`radio-snr`](#radio-snr). Do not rely on one metric alone. |
| 4G versus 5G | [`radio-rat-selected`](#radio-rat-selected) indicates active radio access technology. 5G fields prefixed with `nr5g-` may be zero or unknown when the active technology is 4G. |
| Location | Use [`site-id`](#site-id), [`site-name`](#site-name), [`latitude`](#latitude), [`longitude`](#longitude), and [`isDeviceGeoData`](#isdevicegeodata). Store manual overrides separately. |
| Health rollup | Compare [`health`](#health), [`state`](#state), [`status`](#status), [`state_description`](#state_description), [`reachability`](#reachability), [`controlConnections`](#controlconnections), and [`bfdSessionsUp`](#bfdsessionsup). These fields can disagree because they come from different rollup models or time windows. |

## Dashboard Guidance

- Use [`system-ip`](#system-ip) as the stable join key for device-centric dashboards.
- Use [`site-id`](#site-id) as the stable join key for site-centric dashboards.
- Use [`vdevice-dataKey`](#vdevice-datakey) for interface rows when storing historical samples.
- Show [`if-admin-status`](#if-admin-status) and [`if-oper-status`](#if-oper-status) side by side.
- Treat `health`, `state`, and `status` as rollups, then show the reason using control connections, BFD sessions, interface state, and alarms.
- For cellular dashboards, classify quality using multiple RF metrics and customer-specific thresholds.

