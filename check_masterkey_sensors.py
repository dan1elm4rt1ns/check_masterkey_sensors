#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plugin de Monitoramento Customizado para Sensores MasterKey via SNMP
Nome: check_masterkey_sensors.py
Versão: 2.2 (Modo --all corrigido para usar snmpget, melhorias no help)
"""

import sys
import argparse
import subprocess
import re
import shlex
from collections import namedtuple

# --- Constantes de Status do OpMon ---
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3

# --- Estrutura de Dados e Mapeamento Central de Métricas ---
Metric = namedtuple('Metric', ['oid', 'type', 'unit', 'desc'])

METRICS_MAP = {
    'TempAC1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.0.1', type='Float', unit='°C', desc='Temp. retorno split 1'),
    'TempAC2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.0.2', type='Float', unit='°C', desc='Temp. retorno split 2'),
    'TempAC3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.0.3', type='Float', unit='°C', desc='Temp. retorno split 3'),
    'TempAC4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.0.4', type='Float', unit='°C', desc='Temp. retorno split 4'),
    'StatusAC1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.1.1', type='Inteiro', unit='', desc='Estado de operação do split 1'),
    'StatusAC2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.1.2', type='Inteiro', unit='', desc='Estado de operação do split 2'),
    'StatusAC3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.1.3', type='Inteiro', unit='', desc='Estado de operação do split 3'),
    'StatusAC4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.1.4', type='Inteiro', unit='', desc='Estado de operação do split 4'),
    'AlarmeAC1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.2.1', type='Inteiro', unit='', desc='Status do alarme do split 1'),
    'AlarmeAC2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.2.2', type='Inteiro', unit='', desc='Status do alarme do split 2'),
    'AlarmeAC3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.2.3', type='Inteiro', unit='', desc='Status do alarme do split 3'),
    'AlarmeAC4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.2.4', type='Inteiro', unit='', desc='Status do alarme do split 4'),
    'ConectAC1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.3.5', type='Inteiro', unit='', desc='Status da conexão wifi módulo 1'),
    'ConectAC2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.3.6', type='Inteiro', unit='', desc='Status da conexão wifi módulo 2'),
    'ConectAC3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.3.7', type='Inteiro', unit='', desc='Status da conexão wifi módulo 3'),
    'ConectAC4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.2.3.8', type='Inteiro', unit='', desc='Status da conexão wifi módulo 4'),
    'StatusED1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.1', type='Inteiro', unit='', desc='Estado da entrada digital 1'),
    'StatusED2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.2', type='Inteiro', unit='', desc='Estado da entrada digital 2'),
    'StatusED3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.3', type='Inteiro', unit='', desc='Estado da entrada digital 3'),
    'StatusED4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.4', type='Inteiro', unit='', desc='Estado da entrada digital 4'),
    'StatusED5': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.5', type='Inteiro', unit='', desc='Estado da entrada digital 5'),
    'StatusED6': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.6', type='Inteiro', unit='', desc='Estado da entrada digital 6'),
    'StatusED7': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.7', type='Inteiro', unit='', desc='Estado da entrada digital 7'),
    'StatusED8': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.8', type='Inteiro', unit='', desc='Estado da entrada digital 8'),
    'StatusED9': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.9', type='Inteiro', unit='', desc='Estado da entrada digital 9*'),
    'StatusED10': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.10', type='Inteiro', unit='', desc='Estado da entrada digital 10*'),
    'StatusED11': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.11', type='Inteiro', unit='', desc='Estado da entrada digital 11*'),
    'StatusED12': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.12', type='Inteiro', unit='', desc='Estado da entrada digital 12*'),
    'StatusED13': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.13', type='Inteiro', unit='', desc='Estado da entrada digital 13*'),
    'StatusED14': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.14', type='Inteiro', unit='', desc='Estado da entrada digital 14*'),
    'StatusED15': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.15', type='Inteiro', unit='', desc='Estado da entrada digital 15*'),
    'StatusED16': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.7.16', type='Inteiro', unit='', desc='Estado da entrada digital 16*'),
    'MomED1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.1', type='Inteiro', unit='', desc='Status de alarme entrada digital 1'),
    'MomED2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.2', type='Inteiro', unit='', desc='Status de alarme entrada digital 2'),
    'MomED3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.3', type='Inteiro', unit='', desc='Status de alarme entrada digital 3'),
    'MomED4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.4', type='Inteiro', unit='', desc='Status de alarme entrada digital 4'),
    'MomED5': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.5', type='Inteiro', unit='', desc='Status de alarme entrada digital 5'),
    'MomED6': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.6', type='Inteiro', unit='', desc='Status de alarme entrada digital 6'),
    'MomED7': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.7', type='Inteiro', unit='', desc='Status de alarme entrada digital 7'),
    'MomED8': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.8', type='Inteiro', unit='', desc='Status de alarme entrada digital 8'),
    'MomED9': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.9', type='Inteiro', unit='', desc='Status de alarme entrada digital 9*'),
    'MomED10': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.10', type='Inteiro', unit='', desc='Status de alarme entrada digital 10*'),
    'MomED11': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.11', type='Inteiro', unit='', desc='Status de alarme entrada digital 11*'),
    'MomED12': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.12', type='Inteiro', unit='', desc='Status de alarme entrada digital 12*'),
    'MomED13': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.13', type='Inteiro', unit='', desc='Status de alarme entrada digital 13*'),
    'MomED14': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.14', type='Inteiro', unit='', desc='Status de alarme entrada digital 14*'),
    'MomED15': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.15', type='Inteiro', unit='', desc='Status de alarme entrada digital 15*'),
    'MomED16': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.1.16', type='Inteiro', unit='', desc='Status de alarme entrada digital 16*'),
    'TempMod1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.1', type='Float', unit='°C', desc='Temperatura Sensor Modbus 1'),
    'TempMod2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.2', type='Float', unit='°C', desc='Temperatura Sensor Modbus 2'),
    'TempMod3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.3', type='Float', unit='°C', desc='Temperatura Sensor Modbus 3'),
    'TempMod4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.4', type='Float', unit='°C', desc='Temperatura Sensor Modbus 4'),
    'TempMod5': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.5', type='Float', unit='°C', desc='Temperatura Sensor Modbus 5'),
    'TempMod6': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.6', type='Float', unit='°C', desc='Temperatura Sensor Modbus 6'),
    'TempMod7': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.7', type='Float', unit='°C', desc='Temperatura Sensor Modbus 7'),
    'TempMod8': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.4.8', type='Float', unit='°C', desc='Temperatura Sensor Modbus 8'),
    'UmidMod1': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.1', type='Float', unit='%', desc='Umidade Sensor Modbus 1'),
    'UmidMod2': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.2', type='Float', unit='%', desc='Umidade Sensor Modbus 2'),
    'UmidMod3': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.3', type='Float', unit='%', desc='Umidade Sensor Modbus 3'),
    'UmidMod4': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.4', type='Float', unit='%', desc='Umidade Sensor Modbus 4'),
    'UmidMod5': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.5', type='Float', unit='%', desc='Umidade Sensor Modbus 5'),
    'UmidMod6': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.6', type='Float', unit='%', desc='Umidade Sensor Modbus 6'),
    'UmidMod7': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.7', type='Float', unit='%', desc='Umidade Sensor Modbus 7'),
    'UmidMod8': Metric(oid='.1.3.6.1.4.1.39672.3.5.4.8.0.5.8', type='Float', unit='%', desc='Umidade Sensor Modbus 8'),
}

DEFAULT_THRESHOLDS = {
    'temperature': {'w': 40.0, 'c': 50.0},
    'humidity': {'w': 80.0, 'c': 90.0},
}

class SNMPError(Exception):
    """Exceção para falhas na coleta de dados SNMP."""
    pass

class MetricEvaluationError(Exception):
    """Exceção para falhas na avaliação de uma métrica."""
    pass

def get_snmp_value(host, port, community, oid):
    """Executa snmpget para um único OID e retorna o valor limpo."""
    command = f"snmpget -v2c -c {shlex.quote(community)} -O vq {shlex.quote(host)}:{port} {oid}"
    try:
        proc = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False
        )
        stdout_decoded = proc.stdout.decode('utf-8', errors='ignore')
        stderr_decoded = proc.stderr.decode('utf-8', errors='ignore')

        if proc.returncode != 0:
            error_message = stderr_decoded.strip() or stdout_decoded.strip()
            raise SNMPError(f"Falha ao executar snmpget. Erro: {error_message}")
        
        return stdout_decoded.strip()
    except subprocess.TimeoutExpired:
        raise SNMPError(f"Timeout (10s) ao tentar conectar com {host}:{port}")
    except Exception as e:
        raise SNMPError(f"Erro inesperado na função get_snmp_value: {e}")

def evaluate_metric(metric_name, raw_value, warning, critical, invert=False):
    """
    Avalia um valor coletado, compara com thresholds e retorna status, mensagem e perfdata.
    """
    metric = METRICS_MAP.get(metric_name)
    if not metric:
        raise MetricEvaluationError(f"Métrica '{metric_name}' desconhecida.")

    if metric.type == 'Float':
        try:
            value = float(raw_value)
            if metric.unit in ['°C', '%']:
                value = round(value / 10.0, 1)
        except (ValueError, TypeError):
            raise MetricEvaluationError(f"Valor '{raw_value}' para {metric_name} não é numérico.")
        
        if warning is None and critical is None:
            if 'Temp' in metric_name:
                warning = DEFAULT_THRESHOLDS['temperature']['w']
                critical = DEFAULT_THRESHOLDS['temperature']['c']
            elif 'Umid' in metric_name:
                warning = DEFAULT_THRESHOLDS['humidity']['w']
                critical = DEFAULT_THRESHOLDS['humidity']['c']

        status_code = STATUS_OK
        message = f"{metric_name}={value}{metric.unit}"
        perfdata = f"'{metric_name}'={value}{metric.unit};{warning or ''};{critical or ''};;"

        if critical is not None and value >= critical:
            status_code = STATUS_CRITICAL
        elif warning is not None and value >= warning:
            status_code = STATUS_WARNING
        
        return status_code, message, perfdata

    elif metric.type == 'Inteiro':
        try:
            value = int(raw_value)
        except (ValueError, TypeError):
            raise MetricEvaluationError(f"Valor '{raw_value}' para {metric_name} não é um inteiro.")
            
        normal_value = 0 if not invert else 1
        message = f"{metric.desc} = {value}"

        if value == normal_value:
            return STATUS_OK, f"{metric_name} em estado normal ({message})", ""
        else:
            return STATUS_CRITICAL, f"{metric_name} em estado de alarme ({message})", ""

    return STATUS_UNKNOWN, f"Tipo de métrica desconhecido para {metric_name}", ""

class FormattedArgumentParser(argparse.ArgumentParser):
    """ArgumentParser customizado para exibir erro antes da ajuda."""
    def error(self, message):
        print(f"ERRO: {message}\n", file=sys.stderr)
        self.print_help()
        sys.exit(STATUS_UNKNOWN)

def get_formatted_metrics_help():
    """Formata a lista de métricas em categorias para o help."""
    categories = {
        "Temperaturas AC": [m for m in METRICS_MAP if m.startswith('TempAC')],
        "Status AC": [m for m in METRICS_MAP if m.startswith('StatusAC') or m.startswith('AlarmeAC') or m.startswith('ConectAC')],
        "Entradas Digitais (Estado)": [m for m in METRICS_MAP if m.startswith('StatusED')],
        "Entradas Digitais (Alarme)": [m for m in METRICS_MAP if m.startswith('MomED')],
        "Sensores Modbus (Temperatura)": [m for m in METRICS_MAP if m.startswith('TempMod')],
        "Sensores Modbus (Umidade)": [m for m in METRICS_MAP if m.startswith('UmidMod')],
    }
    help_text = "Métricas disponíveis (agrupadas por categoria):\n"
    for category, names in categories.items():
        help_text += f"\n  {category}:\n"
        for i in range(0, len(names), 4):
            help_text += "    " + "  ".join(names[i:i+4]) + "\n"
    return help_text

def main():
    """Função principal que analisa argumentos e orquestra a execução."""
    parser = FormattedArgumentParser(
        description="Plugin para monitorar sensores de dispositivos MasterKey via SNMP.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=get_formatted_metrics_help() + """
Exemplos de uso:
  1. Checar uma temperatura com thresholds customizados:
     ./check_masterkey_sensors.py -H <host-ip> -C <community> -m TempAC1 -w 40 -c 50

  2. Checar o status de uma porta digital (padrão: 0=OK, 1=CRITICAL):
     ./check_masterkey_sensors.py -H <host-ip> -C <community> -m StatusED1

  3. Checar um status com lógica invertida (1=OK, 0=CRITICAL):
     ./check_masterkey_sensors.py -H <host-ip> -C <community> -m StatusAC1 --invert

  4. Checar a saúde de todos os sensores de uma vez (modo confiável):
     ./check_masterkey_sensors.py -H <host-ip> -C <community> --all
"""
    )
    
    parser.add_argument('-H', '--host', required=True, help="Endereço IP do dispositivo.")
    parser.add_argument('-C', '--community', required=True, help="Comunidade SNMP v2c.")
    parser.add_argument('-p', '--port', default=1161, type=int, help="Porta SNMP (padrão: 1161).")
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-m', '--metric', metavar='NOME_DA_METRICA', choices=METRICS_MAP.keys(), help="Nome da métrica a ser verificada.")
    mode_group.add_argument('--all', action='store_true', help="Verificar todos os sensores (usa múltiplos snmpget para confiabilidade).")

    parser.add_argument('-w', '--warning', type=float, help="Threshold de Warning para métricas numéricas.")
    parser.add_argument('-c', '--critical', type=float, help="Threshold de Critical para métricas numéricas.")
    parser.add_argument('--invert', action='store_true', help="Inverte a lógica para métricas de estado (1=OK, 0=CRITICAL).")
    
    args = parser.parse_args()
    
    status_map = {
        STATUS_OK: "OK",
        STATUS_WARNING: "WARNING",
        STATUS_CRITICAL: "CRITICAL",
        STATUS_UNKNOWN: "UNKNOWN"
    }

    try:
        if args.metric:
            metric_info = METRICS_MAP[args.metric]
            raw_value = get_snmp_value(args.host, args.port, args.community, metric_info.oid)
            status_code, message, perfdata = evaluate_metric(
                args.metric, raw_value, args.warning, args.critical, args.invert
            )
            print(f"{status_map[status_code]}: {message} |{perfdata if perfdata else ''}")
            sys.exit(status_code)

        elif args.all:
            final_status = STATUS_OK
            summary_messages = []
            perfdata_list = []

            for name, metric_info in METRICS_MAP.items():
                try:
                    raw_value = get_snmp_value(args.host, args.port, args.community, metric_info.oid)
                    status_code, message, perfdata = evaluate_metric(name, raw_value, None, None, False)
                    
                    if perfdata:
                        perfdata_list.append(perfdata)

                    if status_code > STATUS_OK:
                        final_status = max(final_status, status_code)
                        summary_messages.append(message)
                
                except (SNMPError, MetricEvaluationError) as e:
                    final_status = max(final_status, STATUS_CRITICAL)
                    summary_messages.append(f"{name}=ERRO({e})")
            
            if not summary_messages:
                print(f"OK: Saúde geral do dispositivo OK. | {' '.join(perfdata_list)}")
            else:
                full_message = f"{len(summary_messages)} problemas encontrados: {', '.join(summary_messages)}"
                print(f"{status_map[final_status]}: {full_message} | {' '.join(perfdata_list)}")
            
            sys.exit(final_status)

    except (SNMPError, MetricEvaluationError) as e:
        # Erros que acontecem no modo de métrica única
        print(f"CRITICAL: {e}")
        sys.exit(STATUS_CRITICAL)
    except Exception as e:
        print(f"UNKNOWN: Ocorreu um erro inesperado no plugin: {e}")
        sys.exit(STATUS_UNKNOWN)

if __name__ == "__main__":
    main()