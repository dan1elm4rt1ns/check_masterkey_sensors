# Nagios Plugin for MasterKey SNMP Monitoring (check_masterkey_sensors)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A custom **Nagios Plugin** written in **Python 3** designed for comprehensive **SNMP monitoring** of **MasterKey** devices. The `check_masterkey_sensors.py` script provides a powerful solution for sysadmins and DevOps teams using **Nagios Core**, **OpMon**, or other Nagios-based systems to monitor up to 64 critical sensors, including **temperature**, **humidity**, and **digital input status**.

This script serves as a custom SNMP check, connecting to the device on a non-standard port (default `1161`) to provide detailed status and **performance data**.

## Key Features for SNMP Monitoring

- **Specific MasterKey Monitoring**: Natively designed to check 64 OIDs related to MasterKey device sensors.
- **Individual Metric Checks**: Provides the ability to monitor a single sensor with custom `Warning` and `Critical` thresholds.
- **Overall Health Check Mode (`--all`)**: A robust mode that performs an SNMP `get` for every metric, providing a complete health summary. Ideal for environments where `snmpwalk` is unstable.
- **Inverted State Logic (`--invert`)**: Supports sensors where an "active" state (1) is the desired normal status.
- **Nagios Performance Data (Perfdata)**: Automatically generates perfdata for all numeric sensors, enabling graphing and trend analysis in tools like PNP4Nagios.
- **Clear, Actionable Output**: Provides detailed status messages and robust error handling to simplify troubleshooting.

## Requirements for this Python SNMP Plugin

- **Nagios Server**: Nagios Core, OpMon, or any Nagios-based compatible system.
- **Python Interpreter**: Python 3.6 or newer.
- **SNMP Tools**: The `net-snmp-utils` package (providing the `snmpget` command) must be installed on the Nagios server.
- **Network Access**: UDP network connectivity from the Nagios server to the MasterKey device on port `1161` (or the specified target port).

## Installation

1.  **Clone the Repository or Download the Script**
    ```bash
    git clone [https://github.com/your-user/your-repo.git](https://github.com/your-user/your-repo.git)
    # Or simply download the check_masterkey_sensors.py file
    ```

2.  **Copy the Plugin to the Nagios Libexec Directory**
    ```bash
    cp check_masterkey_sensors.py /usr/local/nagios/libexec/
    ```

3.  **Assign Execute Permissions**
    ```bash
    chmod +x /usr/local/nagios/libexec/check_masterkey_sensors.py
    ```

## Usage and Command-Line Arguments

The script is executed from the command line with the following syntax:

```bash
./check_masterkey_sensors.py -H <host> -C <community> [OPTIONS]
```

| Argument             | Description                                                                              |
| -------------------- | -------------------------------------------------------------------------------------- |
| `-H`, `--host`       | **(Required)** IP address of the MasterKey device.                                     |
| `-C`, `--community`  | **(Required)** SNMPv2c community string for authentication.                              |
| `-p`, `--port`       | The device's SNMP port. (Default: `1161`).                                             |
| `-m`, `--metric`     | The name of the metric to check (e.g., `TempAC1`). Use with `-w` and `-c`.               |
| `--all`              | Checks all 64 sensors and returns an overall health summary.                           |
| `-w`, `--warning`    | *Warning* threshold for numeric metrics.                                               |
| `-c`, `--critical`   | *Critical* threshold for numeric metrics.                                              |
| `--invert`           | Inverts the state logic for `Integer` sensors (makes `1` = OK and `0` = CRITICAL).     |
| `-h`, `--help`       | Displays the full help message with the list of available metrics.                     |

## Nagios Core / OpMon Configuration Examples

Here are example configurations for your Nagios `commands.cfg` and `services.cfg` files.

### 1. Command Definitions (`commands.cfg`)

These flexible command definitions allow for easy reuse across multiple service checks.

```nagios
# Command to check an individual MasterKey sensor metric
define command {
    command_name    check_masterkey_sensor
    command_line    $USER1$/check_masterkey_sensors.py -H $HOSTADDRESS$ -C $_HOSTSNMPCOMMUNITY$ -m $ARG1$ -w $ARG2$ -c $ARG3$ $ARG4$
}

# Command to check the overall health (all sensors)
define command {
    command_name    check_masterkey_all
    command_line    $USER1$/check_masterkey_sensors.py -H $HOSTADDRESS$ -C $_HOSTSNMPCOMMUNITY$ --all
}
```

### 2. Service Definitions (`services.cfg`)

Use the commands above to define your monitoring services.

**Example 1: Monitor Temperature with Custom Thresholds**

```nagios
define service {
    use                     generic-service
    host_name               masterkey-server
    service_description     SNMP - AC Temperature 1
    check_command           check_masterkey_sensor!TempAC1!40!50
    # ARG1 = TempAC1, ARG2 = Warning at 40°C, ARG3 = Critical at 50°C
}
```

**Example 2: Monitor a Digital Input Status (Standard Logic: 0=OK, 1=CRITICAL)**

```nagios
define service {
    use                     generic-service
    host_name               masterkey-server
    service_description     SNMP - Digital Input Status 2
    check_command           check_masterkey_sensor!StatusED2!!!!
}
```

**Example 3: Monitor an Operational Status with Inverted Logic (1=OK, 0=CRITICAL)**

```nagios
define service {
    use                     generic-service
    host_name               masterkey-server
    service_description     SNMP - Split Operation Status 1
    check_command           check_masterkey_sensor!StatusAC1!!!!--invert
    # ARG4 is used to pass the --invert flag
}
```

**Example 4: Monitor Overall Sensor Health**

```nagios
define service {
    use                     generic-service
    host_name               masterkey-server
    service_description     SNMP - Overall Sensor Health
    check_command           check_masterkey_all
}
```

## MasterKey SNMP OID & Metrics Reference

### Numeric Sensors (Temperatures and Humidity)
The raw integer value returned by the device's SNMP agent is automatically **divided by 10** by this script to produce the final, real-world value.

| Metric Name             | Description                    | Unit |
| ----------------------- | ------------------------------ | ---- |
| `TempAC1` - `TempAC4`   | Split return temperature 1-4   | °C   |
| `TempMod1` - `TempMod8` | Modbus sensor temperature 1-8  | °C   |
| `UmidMod1` - `UmidMod8` | Modbus sensor humidity 1-8     | %    |

### State Sensors (Status and Alarms)
The default logic considers `0` as OK and `1` as CRITICAL. Use the `--invert` flag to reverse this behavior for specific checks.

| Metric Category         | Metric Names                | Default Value Interpretation                              |
| ----------------------- | --------------------------- | --------------------------------------------------------- |
| **Split Operation** | `StatusAC1` - `StatusAC4`   | `0` = Off (OK), `1` = On (CRITICAL)                       |
| **Split Alarm** | `AlarmeAC1` - `AlarmeAC4`   | `0` = Normal (OK), `1` = Alarm (CRITICAL)                 |
| **WiFi Connection** | `ConectAC1` - `ConectAC4`   | `0` = Disconnected (OK), `1` = Connected (CRITICAL)       |
| **Digital Input State** | `StatusED1` - `StatusED16`  | `0` = Closed (OK), `1` = Open (CRITICAL)                  |
| **Digital Input Alarm** | `MomED1` - `MomED16`        | `0` = Normal (OK), `1` = Alarm (CRITICAL)                 |

## Output Format & Performance Data

The plugin uses the standard Nagios output format, which is divided into two parts separated by a "pipe" (`|`):

`STATUS: Text Output | 'perfdata'=value[UOM];[warn];[crit];;`

- **Text Output:** A human-readable description of the sensor's status.
- **Performance Data (perfdata):** Machine-readable data used for graphing and trend analysis.

---

## Keywords / Tags

For search engine optimization and to facilitate discovery, here are keywords associated with this project:

`Nagios, Nagios Core, Nagios Plugin, OpMon, Custom Nagios Plugin, Monitoring, IT-Monitoring, SNMP, SNMPv2c, SNMP Check, Custom SNMP Script, SNMP Monitoring, OID, MasterKey, Sensor Monitoring, Temperature Monitoring, Humidity Monitoring, Digital Input, Python, Python 3, Python Script, Nagios Plugin Python, Python SNMP, Performance Data, Perfdata, Custom Thresholds, Health Check, SysAdmin, DevOps`
