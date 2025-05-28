#!/usr/bin/env python3
import subprocess
import re
import os
import platform
import statistics
import requests
from datetime import datetime
from typing import Dict, Any
from pymongo import MongoClient
from threading import Thread
import time

class DatabaseHandler:
    def __init__(self, db_name="network_analysis", collection_name="test_results"):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_results(self, data: Dict[str, Any]):
        try:
            self.collection.insert_one(data)
            print("Results saved to MongoDB.")
        except Exception as e:
            print(f"Error saving to database: {e}")

    def get_last_test_latency(self):
            try:
                last_result = self.collection.find_one(
                    {}, sort=[("timestamp", -1)]
                )  # Obter o último teste
                if last_result and "performance_results" in last_result:
                    avg_latency = last_result["performance_results"].get("Avg")
                    if avg_latency:
                        return float(avg_latency.split()[0])  # Extrair o valor numérico
                return None
            except Exception as e:
                print(f"Error retrieving last test latency: {e}")
                return None

class NetworkAnalyzer:
    def __init__(self):
        self.os_type = platform.system().lower()
    
    def run_command(self, command, shell=True):
        try:
            process = subprocess.run(
                command, shell=shell, capture_output=True, text=True
            )
            return process.stdout
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            return None

    def get_linux_info(self):
        network_info = {
            'IP_Address': None,
            'Subnet_Mask': None,
            'Default_Gateway': None,
            'DNS_Servers': [],
        }

        iw_output = self.run_command("iwconfig 2>/dev/null | grep -o '^[[:alnum:]]*'")
        if not iw_output:
            print("No wireless interface found")
            return None
        interface = iw_output.split('\n')[0].strip()

        ip_output = self.run_command(f"ip addr show {interface}")
        if ip_output:
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', ip_output)
            if ip_match:
                network_info['IP_Address'] = ip_match.group(1)
                cidr_mask = int(ip_match.group(2))
                network_info['Subnet_Mask'] = self.cidr_to_netmask(cidr_mask)
        
        gateway_output = self.run_command("ip route | grep default")
        if gateway_output:
            gateway_match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', gateway_output)
            if gateway_match:
                network_info['Default_Gateway'] = gateway_match.group(1)

        if os.path.exists('/etc/resolv.conf'):
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    if line.startswith('nameserver'):
                        network_info['DNS_Servers'].append(line.split()[1].strip())
        return network_info

    def cidr_to_netmask(self, cidr):
        """Converte um valor CIDR para o formato de máscara decimal."""
        bits = (1 << 32) - (1 << 32 >> cidr)
        return '.'.join(str((bits >> (i * 8)) & 0xFF) for i in range(4)[::-1])

    def get_network_info(self):
        if self.os_type == 'linux':
            return self.get_linux_info()
        else:
            print(f"Unsupported operating system: {self.os_type}")
            return None

class WifiAnalyzer:
    def get_connected_wifi_info(self):
        try:
            # Verificar a interface sem fio conectada
            iw_output = subprocess.getoutput("iw dev")
            interface_match = re.search(r'Interface (\S+)', iw_output)
            if not interface_match:
                print("No wireless interface found")
                return {}

            interface = interface_match.group(1)
            signal_data = self.get_signal_strength_and_quality(interface)

            # Obter informações detalhadas sobre a conexão
            info_output = subprocess.getoutput(f"iw dev {interface} link")
            
            # Obter a frequência
            freq_match = re.search(r'freq: (\d+)', info_output)
            if not freq_match:
                print("Frequency not found")
                return {}
            frequency = int(freq_match.group(1)) / 1000  # Converter para GHz

            # Obter o canal
            info_output2 = subprocess.getoutput(f"iw dev {interface} info")
            channel_match = re.search(r'channel (\d+)', info_output2)
            if not channel_match:
                print("Channel not found")
                return {}
            channel = int(channel_match.group(1))

            return {
                "SSID": self.get_connected_ssid(),
                "Frequency": f"{frequency:.4} GHz",
                "Channel": channel,
                **signal_data
            }
        except Exception as e:
            print(f"Error getting WiFi info: {e}")
            return {}

    def get_connected_ssid(self):
        """Obtém o SSID da rede Wi-Fi conectada"""
        output = subprocess.getoutput("iwgetid")
        ssid_match = re.search(r'\"(.+)\"', output)
        return ssid_match.group(1) if ssid_match else "Unknown"

    def get_signal_strength_and_quality(self, interface):
        """Obtém a intensidade do sinal da rede conectada e determina a qualidade"""
        try:
            output = subprocess.getoutput(f"iw dev {interface} link")
            signal_match = re.search(r'signal: (-?\d+)', output)
            
            if signal_match:
                rssi = int(signal_match.group(1))
                quality = None

                # Determinar a qualidade do sinal
                if rssi > -50:
                    quality = "Excelent"
                elif -51 <= rssi <= -60:
                    quality = "Good"
                elif -61 <= rssi <= -70:
                    quality = "Fair"
                else:
                    quality = "Weak"

                return {
                    "RSSI": f"{rssi} dBm",
                    "Signal Quality": quality
                }
            else:
                return {
                    "RSSI": "Unknown",
                    "Signal Quality": "Unknown"
                }
        except Exception as e:
            print(f"Error getting signal strength: {e}")
            return {
                "RSSI": "Unknown",
                "Signal Quality": "Unknown"
            }

class NetworkPerformanceTester:
    def test_gateway_ping(self):
        #Test ping to local gateway
        try:
            # Get the default gateway from network info
            network_analyzer = NetworkAnalyzer()
            network_info = network_analyzer.get_network_info()
            
            if not network_info or not network_info.get('Default_Gateway'):
                print("Unable to retrieve default gateway")
                return None

            gateway = network_info['Default_Gateway']
            
            # Run ping test to gateway
            stdout = subprocess.getoutput(f"ping -c 300 -i 0.1 {gateway}")
            times = [float(m.group(1)) for m in re.finditer(r'time=(\d+\.?\d*)', stdout)]
            packet_loss_match = re.search(r'(\d+)% packet loss', stdout)
            packet_loss = int(packet_loss_match.group(1)) if packet_loss_match else None
            
            return {
                'Gateway': gateway,
                'Min ': f"{min(times):.2f} ms" if times else "N/A",
                'Max': f"{max(times):.2f} ms" if times else "N/A",
                'Avg': f"{statistics.mean(times):.2f} ms" if times else "N/A",
                'Packet Loss': f"{packet_loss} %" if packet_loss is not None else "N/A",
            }
        except Exception as e:
            print(f"Error in gateway ping test: {e}")
            return None    
    
    def __init__(self):
        self.google_dns = "8.8.8.8"
        self.download_url = "https://speed.cloudflare.com/__down?bytes=25000000"  # 25MB test file
        self.upload_url = "https://speed.cloudflare.com/__up"

    def test_dns(self):
        """Testa conectividade com DNS e capacidade de resolução usando o DNS do sistema Linux"""
        results = {
            'DNS_Server': 'Unknown',
            'Port_Test': 'Failed',
            'Resolution_Test': 'Failed',
            'Resolved_IPs': []
        }

        try:
            # Obtém o DNS do sistema Linux usando NetworkAnalyzer
            network_analyzer = NetworkAnalyzer()
            network_info = network_analyzer.get_linux_info()
            
            if network_info and network_info.get('DNS_Servers'):
                # Usa o primeiro servidor DNS da lista
                dns_ip = network_info['DNS_Servers'][0]
                results['DNS_Server'] = dns_ip

                # Testa conectividade na porta 53 (DNS)
                try:
                    nc_output = subprocess.getoutput(f"nc -zv {dns_ip} 53 2>&1")
                    if 'succeeded' in nc_output.lower():
                        results['Port_Test'] = 'Success'
                    else:
                        results['Port_Test'] = 'Failed'
                        results['Port_Test_Error'] = nc_output.strip()
                except Exception as e:
                    results['Port_Test'] = 'Failed'
                    results['Port_Test_Error'] = str(e)

                # Testa resolução DNS
                try:
                    nslookup_output = subprocess.getoutput(f"nslookup www.google.com {dns_ip}")
                    if 'Address:' in nslookup_output:
                        results['Resolution_Test'] = 'Success'
                        for line in nslookup_output.splitlines():
                            if 'Address:' in line and not line.endswith(dns_ip):
                                ip = line.split('Address:')[-1].strip()
                                results['Resolved_IPs'].append(ip)
                    else:
                        results['Resolution_Test'] = 'Failed'
                        results['Resolution_Test_Error'] = nslookup_output.strip()
                except Exception as e:
                    results['Resolution_Test'] = 'Failed'
                    results['Resolution_Test_Error'] = str(e)

        except Exception as e:
            print(f"Erro no teste de DNS: {e}")
            results['Error'] = str(e)

        return results

    def test_ping(self, count=300, interval=0.1):
        try:
            stdout = subprocess.getoutput(f"ping -c {count} -i {interval} {self.google_dns}")
            times = [float(m.group(1)) for m in re.finditer(r'time=(\d+\.?\d*)', stdout)]
            packet_loss_match = re.search(r'(\d+)% packet loss', stdout)
            packet_loss = int(packet_loss_match.group(1)) if packet_loss_match else None
            return {
                'Min': f"{min(times):.2f} ms",
                'Max': f"{max(times):.2f} ms",
                'Avg': f"{statistics.mean(times):.2f} ms",
                'Packet Loss': f"{packet_loss} %",
            } if times else None
        except Exception as e:
            print(f"Error in ping test: {e}")
            return None

    def test_mtr(self):
        try:
            output = subprocess.getoutput(f"mtr -rn -c 10 --report-wide {self.google_dns}")
            hops_data = []
            for line in output.splitlines()[2:]:  # Ignorar cabeçalho
                parts = line.split()
                if len(parts) < 8:  # Verificar formato esperado
                    continue
                
                #Extrair dados
                raw_hop = parts[0].strip()
                hop_match = re.match(r'(\d+)', raw_hop)
                hop = hop_match.group(1) if hop_match else "?"
                host = parts[1].strip()
                loss = float(parts[2].strip('%'))
                avg_latency = float(parts[7])

                hops_data.append({
                    "Hop": hop,
                    "Host": host,
                    "Loss": f"{loss} %",
                    "Latency": f"{avg_latency} ms"
                })

            return hops_data
        except Exception as e:
            print(f"Error in MTR test: {e}")
            return []

    def get_connection_info(self):
        """Get IP, ISP, Primary DNS and location information"""
        try:
            # Inicializar dicionário de retorno
            connection_info = {
                'IPv4': 'Unknown',
                'ISP': 'Unknown',
                'Location': 'Unknown',
                'Primary DNS': 'Unknown',
            }

            # Coletar informações de IP e ISP
            ip_info_response = requests.get('http://ip-api.com/json/')
            if ip_info_response.status_code == 200:
                ip_info = ip_info_response.json()
                if ip_info.get('status') == 'success':
                    connection_info.update({
                        'IPv4': ip_info.get('query', 'Unknown'),
                        'ISP': ip_info.get('isp', 'Unknown'),
                        'Location': f"{ip_info.get('city', '')}, {ip_info.get('country', '')}"
                    })

            # Coletar DNS do ISP
            dns_info_response = requests.get('https://edns.ip-api.com/json')
            if dns_info_response.status_code == 200:
                dns_info = dns_info_response.json()
                connection_info['Primary DNS'] = dns_info.get('dns', {}).get('ip', 'Unknown')

            return connection_info

        except requests.exceptions.RequestException as e:
            print(f"Error fetching connection info: {e}")
            return {
                'IPv4': 'Unknown',
                'ISP': 'Unknown',
                'Location': 'Unknown',
                'Primary DNS': 'Unknown',
            }

    def test_bandwidth(self, duration=60):
        """Test download and upload speeds."""
        try:
            # Get connection info first
            connection_info = self.get_connection_info()

            # Test download speed
            start_time = time.time()
            response = requests.get(self.download_url, stream=True)
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded += len(chunk)
                if time.time() - start_time >= duration:
                    break
            
            download_speed = (downloaded * 8) / (time.time() - start_time) / 1000000  # Mbps
            
            # Test upload speed
            data = os.urandom(1000000)  # 1MB of random data
            start_time = time.time()
            uploaded = 0
            while time.time() - start_time < duration:
                response = requests.post(self.upload_url, data=data)
                if response.status_code == 200:
                    uploaded += len(data)
            
            upload_speed = (uploaded * 8) / (time.time() - start_time) / 1000000  # Mbps
                        
            # Return all results
            results = {
                'bandwidth': {
                    'Download': f"{round(download_speed, 2)} Mbps",
                    'Upload': f"{round(upload_speed, 2)} Mbps"
                },
                'connection_info': connection_info,
                'dns_tests': self.test_dns()
            }
            return results
            
        except Exception as e:
            print(f"Error testing bandwidth: {e}")
            return {
                'bandwidth': {
                    'Download': 'N/A',
                    'Upload': 'N/A'
                },
                'connection_info': {
                    'IPv4': 'Unknown',
                    'Primary DNS': 'Unkown',
                    'ISP': 'Unknown',
                    'Location': 'Unknown'
                },
                'dns_tests': {
                    'DNS_Server': 'Unknown',
                    'Port_Test': 'Error',
                    'Resolution_Test': 'Error'
                }
            }

class HTMLExporter:
    @staticmethod
    def format_for_dashboard(
        network_info: Dict[str, Any],
        wifi_info: Dict[str, Any],
        performance_results: Dict[str, Any],
        gateway_ping_results: Dict[str,Any],
        mtr_results: list,
        bandwidth_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format results for dashboard display"""
        connection_info = bandwidth_results.get('connection_info', {})
        bandwidth_data = bandwidth_results.get('bandwidth', {})
        dns_tests = bandwidth_results.get('dns_tests', {})
        
        # Process DNS test results
        formatted_dns_results = {
            'DNS_Server': dns_tests.get('DNS_Server', 'Unknown'),
            'Port_Test': {
                'Status': dns_tests.get('Port_Test', 'Unknown'),
                'Error': dns_tests.get('Port_Test_Error', '')
            },
            'Resolution_Test': {
                'Status': dns_tests.get('Resolution_Test', 'Unknown'),
                'Error': dns_tests.get('Resolution_Test_Error', ''),
                'Resolved_IPs': dns_tests.get('Resolved_IPs', [])
            }
        }
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'network_info': network_info,
            'wifi_info': wifi_info,
            'performance_results': performance_results,
            'gateway_ping_results': gateway_ping_results,
            'mtr_results': mtr_results,
            'connection_info': connection_info,
            'bandwidth_data': bandwidth_data,
        }

    @staticmethod
    def save_to_mongo(formatted_results: Dict[str, Any], db_handler: DatabaseHandler):
        """Save formatted results to MongoDB"""
        db_handler.save_results(formatted_results)
        
def execute_main_code():
    # Instanciar as classes necessárias
    analyzer = NetworkAnalyzer()
    wifi_analyzer = WifiAnalyzer()
    tester = NetworkPerformanceTester()
    db_handler = DatabaseHandler()

    # Executar os testes de rede
    performance_results = tester.test_ping()
    gateway_ping_results = tester.test_gateway_ping()
    mtr_results = tester.test_mtr()
    bandwidth_results = tester.test_bandwidth()

    # Garantir que dns_results seja sempre definido
    dns_results = {}

    try:
        dns_results = tester.test_dns()
        if dns_results is None:  # Caso a função retorne None, definir como dicionário vazio
            dns_results = {}
    except Exception as e:
        print(f"Erro ao testar DNS: {e}")
        dns_results = {}

    # Adicionar os resultados do DNS ao dicionário de bandwidth_results
    bandwidth_results['dns_tests'] = dns_results

    # Obter informações da rede
    network_info = analyzer.get_network_info()
    wifi_info = wifi_analyzer.get_connected_wifi_info()

    # Consolidar resultados
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "network_info": network_info,
        "wifi_info": wifi_info,
        "performance_results": performance_results,
        "gateway_ping_results": gateway_ping_results,
        "mtr_results": mtr_results,
        "bandwidth_results": bandwidth_results  # Agora inclui os testes de DNS
    }

    # Salvar os resultados no banco de dados
    db_handler.save_results(results)

    # Formatar os resultados para o dashboard
    formatted_results = HTMLExporter.format_for_dashboard(
        network_info, wifi_info, performance_results, gateway_ping_results, mtr_results, bandwidth_results
    )
    HTMLExporter.save_to_mongo(formatted_results, db_handler)

    # Retornar a latência média para monitoramento
    return float(performance_results["Avg"].split()[0]) if performance_results else None

def background_ping_monitor(last_latency):
    tester = NetworkPerformanceTester()
    analyzer = NetworkAnalyzer()
    db_handler = DatabaseHandler()
    
    # Get initial gateway ping results
    gateway_results = tester.test_gateway_ping()
    last_gateway_latency = float(gateway_results["Avg"].split()[0]) if gateway_results else None

    while True:
        time.sleep(60)  # Changed to 60-second interval
        print("Running gateway ping test...")
        
        # Test gateway latency first
        new_gateway_results = tester.test_gateway_ping()
        if not new_gateway_results or "Avg" not in new_gateway_results:
            print("LAN ping test failed or no average latency available.")
            continue
            
        new_gateway_latency = float(new_gateway_results["Avg"].split()[0])
        print(f"New LAN latency: {new_gateway_latency} ms (Last: {last_gateway_latency} ms)")

        # Calculate gateway latency variation
        gateway_variation = abs(new_gateway_latency - last_gateway_latency) / last_gateway_latency if last_gateway_latency else 0

        # Only proceed with WAN test if gateway variation exceeds threshold
        if gateway_variation >= 0.1:
            print("Gateway latency variation exceeds 10%. Testing WAN latency...")
            
            # Test internet latency
            new_results = tester.test_ping()
            if not new_results or "Avg" not in new_results:
                print("WAN ping test failed or no average latency available.")
                continue
            
            new_latency = float(new_results["Avg"].split()[0])
            print(f"New WAN latency: {new_latency} ms (Last: {last_latency} ms)")

            # Calculate internet latency variation
            internet_variation = abs(new_latency - last_latency) / last_latency if last_latency else 0

            # Only re-execute main code if both variations exceed threshold
            if internet_variation >= 0.1:
                print("Both Gateway and WAN latency variations exceed 10%. Re-executing main code.")
                last_latency = execute_main_code()  # Update both latencies after re-execution
                gateway_results = tester.test_gateway_ping()
                last_gateway_latency = float(gateway_results["Avg"].split()[0]) if gateway_results else None
            else:
                print("WAN latency variation within acceptable range. Continuing monitoring.")
                last_latency = new_latency
                last_gateway_latency = new_gateway_latency
        else:
            print("Gateway latency variation within acceptable range. Continuing monitoring.")
            last_gateway_latency = new_gateway_latency

if __name__ == "__main__":
    # Executar o código principal inicialmente
    last_latency = execute_main_code()

    # Iniciar a thread de monitoramento em segundo plano
    monitor_thread = Thread(target=background_ping_monitor, args=(last_latency,))
    monitor_thread.daemon = True  # Permitir que o programa principal finalize a thread
    monitor_thread.start()

    # Manter o programa em execução
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")