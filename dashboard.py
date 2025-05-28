from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import numpy as np
import os


app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['network_analysis']
collection = db['test_results']

# Create templates directory
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

def calculate_average(values):
    return sum(values) / len(values) if values else 0

@app.route('/')
def dashboard():
    return render_template('resume.html')

@app.route('/graphs')
def area_charts():
    return render_template('graphs.html')

@app.route('/api/ssids', methods=['GET'])
def get_ssids():
    # Busca SSIDs únicos dos últimos 7 dias
    time_threshold = datetime.now() - timedelta(days=7)
    ssids = collection.distinct(
        'wifi_info.SSID',
        {'timestamp': {'$gte': time_threshold.strftime('%d/%m/%Y %H:%M:%S')}}
    )
    return jsonify(list(filter(None, ssids)))  # Remove None/null values

@app.route('/api/history/metrics', methods=['GET'])
def get_metrics_history():
    hours = int(request.args.get('hours', 24))
    ssid = request.args.get('ssid', 'all')
    
    time_threshold = datetime.now() - timedelta(hours=hours)
    
    # Base query
    query = {
        "timestamp": {"$gte": time_threshold.strftime('%Y-%m-%d %H:%M:%S')}
    }
    
    # Add SSID filter if specified
    if ssid != 'all':
        query['wifi_info.SSID'] = ssid
    
    results = list(collection.find(
        query,
        {"timestamp": 1, "gateway_ping_results": 1, "wifi_info": 1, "performance_results": 1, "bandwidth_results": 1}
    ))

    metrics = {
        "timestamps": [],
        "gateway_latency": [],
        "wifi_signal": [],
        "internet_latency": [],
        "download_speed": [],
        "upload_speed": [],
        "gateway_packet_loss": [],
        "internet_packet_loss": []
    }

    for result in results:
        try:
            # Timestamp
            metrics["timestamps"].append(result.get("timestamp"))

            # Gateway Latency
            if result.get('gateway_ping_results') and 'Avg' in result['gateway_ping_results']:
                gateway_latency = float(result['gateway_ping_results']['Avg'].split()[0])
                metrics["gateway_latency"].append(gateway_latency)
            else:
                metrics["gateway_latency"].append(None)
                
            # Gateway Packet Loss
            if result.get('gateway_ping_results') and 'Packet Loss' in result['gateway_ping_results']:
                gateway_packet_loss = float(result['gateway_ping_results']['Packet Loss'].split()[0])
                metrics["gateway_packet_loss"].append(gateway_packet_loss)
            else:
                metrics["gateway_packet_loss"].append(None)

            # Internet Packet Loss
            if result.get('performance_results') and 'Packet Loss' in result['performance_results']:
                internet_packet_loss = float(result['performance_results']['Packet Loss'].split()[0])
                metrics["internet_packet_loss"].append(internet_packet_loss)
            else:
                metrics["internet_packet_loss"].append(None)

            # WiFi Signal
            if result.get('wifi_info') and 'RSSI' in result['wifi_info']:
                wifi_signal = float(result['wifi_info']['RSSI'].split()[0])
                metrics["wifi_signal"].append(wifi_signal)
            else:
                metrics["wifi_signal"].append(None)

            # Internet Latency
            if result.get('performance_results') and 'Avg' in result['performance_results']:
                internet_latency = float(result['performance_results']['Avg'].split()[0])
                metrics["internet_latency"].append(internet_latency)
            else:
                metrics["internet_latency"].append(None)

            # Download and Upload Speeds
            if 'bandwidth_results' in result and 'bandwidth' in result['bandwidth_results']:
                bandwidth_data = result['bandwidth_results']['bandwidth']
                
                # Download Speed
                if isinstance(bandwidth_data, dict) and 'Download' in bandwidth_data:
                    try:
                        download_speed = float(bandwidth_data['Download'].split()[0])
                        metrics["download_speed"].append(download_speed)
                    except (ValueError, AttributeError):
                        metrics["download_speed"].append(None)
                else:
                    metrics["download_speed"].append(None)

                # Upload Speed
                if isinstance(bandwidth_data, dict) and 'Upload' in bandwidth_data:
                    try:
                        upload_speed = float(bandwidth_data['Upload'].split()[0])
                        metrics["upload_speed"].append(upload_speed)
                    except (ValueError, AttributeError):
                        metrics["upload_speed"].append(None)
                else:
                    metrics["upload_speed"].append(None)
            else:
                metrics["download_speed"].append(None)
                metrics["upload_speed"].append(None)

        except (ValueError, AttributeError, KeyError) as e:
            print(f"Error processing result: {e}")
            # Only append None to metrics that haven't been processed yet
            if len(metrics["gateway_latency"]) < len(metrics["timestamps"]):
                metrics["gateway_latency"].append(None)
            if len(metrics["wifi_signal"]) < len(metrics["timestamps"]):
                metrics["wifi_signal"].append(None)
            if len(metrics["internet_latency"]) < len(metrics["timestamps"]):
                metrics["internet_latency"].append(None)
            if len(metrics["download_speed"]) < len(metrics["timestamps"]):
                metrics["download_speed"].append(None)
            if len(metrics["upload_speed"]) < len(metrics["timestamps"]):
                metrics["upload_speed"].append(None)
            if len(metrics["gateway_packet_loss"]) < len(metrics["timestamps"]):
                metrics["gateway_packet_loss"].append(None)
            if len(metrics["internet_packet_loss"]) < len(metrics["timestamps"]):
                metrics["internet_packet_loss"].append(None)

    return jsonify(metrics)

@app.route('/report')
def report():
    last_result = collection.find_one({}, sort=[("timestamp", -1)])
    if not last_result:
        return "No data available", 404

    # Processar dados para o template
    gateway_ping_results = last_result.get('gateway_ping_results', {})
    network_info = {
        'IP Address': last_result.get('network_info', {}).get('IP_Address', 'Unknown'),
        'Subnet Mask': last_result.get('network_info', {}).get('Subnet_Mask', 'Unknown'),
        'Gateway': last_result.get('network_info', {}).get('Default_Gateway', 'Unknown'),
        'DNS Servers': last_result.get('network_info', {}).get('DNS_Servers', []),
        'gateway_latency_min': gateway_ping_results.get('Min', 'N/A'),
        'gateway_latency_max': gateway_ping_results.get('Max', 'N/A'),
        'gateway_latency_avg': gateway_ping_results.get('Avg', 'N/A'),
        'gateway_packet_loss': gateway_ping_results.get('Packet Loss', 'N/A'),
    }

    wifi_info = last_result.get('wifi_info', {})
        
    performance_results = last_result.get('performance_results', {})
    
    connection_info = last_result.get('bandwidth_results', {}).get('connection_info', {})
    {
        'IPv4': last_result.get('IPv4', 'Unknown'),
        'ISP': last_result.get('ISP', 'Unknown'),
        'Primary DNS': last_result.get('Primary DNS','Unknown'),
        'Location': last_result.get('Location', 'Unknown'),
    }

    mtr_results = last_result.get('mtr_results', [])
    for hop in mtr_results:
        loss_str = hop.get('Loss', '0%')
        loss = float(loss_str.strip('%')) if '%' in loss_str else 0.0
        if loss > 20:
            hop['Color'] = '#fca5a5'  # Vermelho para perda > 20%
        elif loss > 5:
            hop['Color'] = '#fde68a'  # Amarelo para perda > 5% e <= 20%
        else:
            hop['Color'] = '#86efac'  # Verde para perda <= 5%

    bandwidth_data = last_result.get('bandwidth_results', {}).get('bandwidth', {})
    
    dns_results = last_result.get('bandwidth_results', {}).get('dns_tests', {})

    # Funções auxiliares para o template
    def format_signal_quality(rssi_str):
        try:
            rssi = float(rssi_str.split()[0])
        except:
            return "N/A"
        if rssi >= -50:
            return "Excellent"
        elif rssi >= -60:
            return "Good"
        elif rssi >= -70:
            return "Fair"
        else:
            return "Poor"

    # Timestamp do relatório
    report_timestamp = last_result.get('timestamp', datetime.now())
    try:
        report_timestamp = datetime.strptime(report_timestamp, '%d/%m/%Y %H:%M:%S')
    except:
        report_timestamp = datetime.now()

    # Formatar a data antes de enviar para o template
    report_timestamp = report_timestamp.strftime('%d/%m/%Y %H:%M:%S')

    return render_template(
        'report.html',
        network_info=network_info,
        wifi_info=wifi_info,
        performance_results=performance_results,
        connection_info=connection_info,
        mtr_results=mtr_results,
        bandwidth_data=bandwidth_data,
        dns_results=dns_results,
        report_timestamp=report_timestamp
    )
    
@app.route('/api/report/last', methods=['GET'])
def get_last_report():
    last_result = collection.find_one({}, sort=[("timestamp", -1)])
    return jsonify(last_result)

def calculate_percentile(values):
    """Calculate the 95 percentile of a list of values"""
    if not values:
        return None
    return float(np.percentile(values, 95))

def generate_insights(data):
    """Gera insights baseados nos dados de métricas da rede."""
    insights = []

    # Analisando o sinal WiFi
    rssi = data.get('local_network', {}).get('rssi', {})
    if rssi and rssi.get('current') is not None:
        current_rssi = rssi['current']
        p95_rssi = rssi.get('p95', current_rssi)

        if current_rssi < -60 or p95_rssi < -75:
            insights.append({
                'type': 'warning',
                'metric': 'WiFi Signal',
                'message': 'Weak WiFi signal detected. May cause frequent disconnections.',
                'value': f'{current_rssi} dBm',
                'threshold': '-60 dBm'
            })
        elif current_rssi > -50 and p95_rssi > -55:
            insights.append({
                'type': 'info',
                'metric': 'WiFi Signal',
                'message': 'Strong WiFi signal detected. Your network is great!',
                'value': f'{current_rssi} dBm',
                'threshold': '-50 dBm'
            })

    # Latência alta na Internet
    latency = data.get('internet', {}).get('latency', {})
    if latency and latency.get('current') is not None:
        current_latency = latency['current']
        p95_latency = latency.get('p95', current_latency)

        if current_latency > 50 or p95_latency > 150:
            insights.append({
                'type': 'critical',
                'metric': 'Internet Latency',
                'message': 'High packet loss may cause connection failures and call freezing.',
                'value': f'{current_latency} ms',
                'threshold': '50 ms'
            })

    # Perda de Pacotes
    packet_loss = data.get('internet', {}).get('packet_loss', {})
    if packet_loss and packet_loss.get('current') is not None:
        current_loss = round(packet_loss['current'], 1)
        p95_loss = round(packet_loss.get('p95', current_loss), 1)

        if current_loss >= 10 or p95_loss >= 50:
            insights.append({
                'type': 'critical',
                'metric': 'Packet Loss',
                'message': 'High packet loss may cause connection failures and call freezing.',
                'value': f'{current_loss}%',
                'threshold': '10%'
            })

    # Velocidade de Download
    download_speed = data.get('internet', {}).get('speed', {}).get('download', {})
    if download_speed and download_speed.get('current') is not None:
        current_download = download_speed['current']
        p95_download = download_speed.get('p95', current_download)

        if current_download < 80 or p95_download < 150:
            insights.append({
                'type': 'warning',
                'metric': 'Download Speed',
                'message': 'Your download speed is below the recommended.',
                'value': f'{current_download} Mbps',
                'threshold': '80 Mbps'
            })

    # Caso nenhum problema seja detectado
    if not insights:
        insights.append({
            'type': 'info',
            'metric': 'Network Health',
            'message': 'No issues detected! Your network is working well.',
            'value': '✅',
            'threshold': 'N/A'
        })

    return insights

@app.route('/api/summary', methods=['GET'])
def get_summary():
    time_threshold = datetime.now() - timedelta(hours=24)
    results = list(collection.find({"timestamp": {"$gte": time_threshold.strftime('%Y-%m-%d %H:%M:%S')}}))
    
    if not results:
        return jsonify({"error": "No data available"})

    # Initialize metric lists
    gateway_latencies = []
    gateway_packet_losses = []
    rssi_values = []
    internet_latencies = []
    internet_packet_losses = []
    download_speeds = []
    upload_speeds = []

    # Process results
    for result in results:
        try:
            # Gateway Metrics
            gateway_results = result.get('gateway_ping_results', {})
            if gateway_results:
                try:
                    if 'Avg' in gateway_results:
                        avg_value = gateway_results['Avg']
                        if isinstance(avg_value, str):
                            gateway_latencies.append(float(avg_value.split()[0]))
                        elif isinstance(avg_value, (int, float)):
                            gateway_latencies.append(float(avg_value))
                            
                    if 'Packet Loss' in gateway_results:
                        loss_value = gateway_results['Packet Loss']
                        if isinstance(loss_value, str):
                            # Remove '%' if present and convert to float
                            loss_value = loss_value.replace('%', '').strip()
                            gateway_packet_losses.append(float(loss_value))
                        elif isinstance(loss_value, (int, float)):
                            gateway_packet_losses.append(float(loss_value))
                except (ValueError, IndexError) as e:
                    print(f"Error processing gateway metrics: {e}")
            
            # RSSI Values
            wifi_info = result.get('wifi_info', {})
            if wifi_info and 'RSSI' in wifi_info:
                try:
                    rssi_value = wifi_info['RSSI']
                    if isinstance(rssi_value, str):
                        rssi_values.append(float(rssi_value.split()[0]))
                    elif isinstance(rssi_value, (int, float)):
                        rssi_values.append(float(rssi_value))
                except (ValueError, IndexError):
                    pass

            # Internet Metrics
            performance_results = result.get('performance_results', {})
            if performance_results:
                try:
                    if 'Avg' in performance_results:
                        avg_value = performance_results['Avg']
                        if isinstance(avg_value, str):
                            internet_latencies.append(float(avg_value.split()[0]))
                        elif isinstance(avg_value, (int, float)):
                            internet_latencies.append(float(avg_value))
                            
                    if 'Packet Loss' in performance_results:
                        loss_value = performance_results['Packet Loss']
                        if isinstance(loss_value, str):
                            # Remove '%' if present and convert to float
                            loss_value = loss_value.replace('%', '').strip()
                            internet_packet_losses.append(float(loss_value))
                        elif isinstance(loss_value, (int, float)):
                            internet_packet_losses.append(float(loss_value))
                except (ValueError, IndexError) as e:
                    print(f"Error processing internet metrics: {e}")

            # Bandwidth Metrics
            bandwidth_results = result.get('bandwidth_results', {}).get('bandwidth', {})
            if isinstance(bandwidth_results, dict):
                if 'Download' in bandwidth_results:
                    try:
                        download_value = bandwidth_results['Download']
                        if isinstance(download_value, str):
                            download_speeds.append(float(download_value.split()[0]))
                        elif isinstance(download_value, (int, float)):
                            download_speeds.append(float(download_value))
                    except (ValueError, IndexError):
                        pass
                        
                if 'Upload' in bandwidth_results:
                    try:
                        upload_value = bandwidth_results['Upload']
                        if isinstance(upload_value, str):
                            upload_speeds.append(float(upload_value.split()[0]))
                        elif isinstance(upload_value, (int, float)):
                            upload_speeds.append(float(upload_value))
                    except (ValueError, IndexError):
                        pass

        except Exception as e:
            print(f"Error processing result: {e}")
            continue

    # Prepare summary response with 95th percentile
    summary = {
        "local_network": {
            "gateway_latency": {
                "current": gateway_latencies[-1] if gateway_latencies else None,
                "p95": calculate_percentile(gateway_latencies),  # Key changed to "p95"
                "min": min(gateway_latencies) if gateway_latencies else None,
                "max": max(gateway_latencies) if gateway_latencies else None
            },
            "gateway_packet_loss": {
                "current": gateway_packet_losses[-1] if gateway_packet_losses else None,
                "p95": calculate_percentile(gateway_packet_losses)  # Key changed to "p95"
            },
            "rssi": {
                "current": rssi_values[-1] if rssi_values else None,
                "p95": calculate_percentile(rssi_values)  # Key changed to "p95"
            }
        },
        "internet": {
            "latency": {
                "current": internet_latencies[-1] if internet_latencies else None,
                "p95": calculate_percentile(internet_latencies),  # Key changed to "p95"
                "min": min(internet_latencies) if internet_latencies else None,
                "max": max(internet_latencies) if internet_latencies else None
            },
            "packet_loss": {
                "current": internet_packet_losses[-1] if internet_packet_losses else None,
                "p95": calculate_percentile(internet_packet_losses)  # Key changed to "p95"
            },
            "speed": {
                "download": {
                    "current": download_speeds[-1] if download_speeds else None,
                    "p95": calculate_percentile(download_speeds)  # Key changed to "p95"
                },
                "upload": {
                    "current": upload_speeds[-1] if upload_speeds else None,
                    "p95": calculate_percentile(upload_speeds)  # Key changed to "p95"
                }
            }
        },
    }
    
    summary['insights'] = generate_insights(summary)
    
    return jsonify(summary)

@app.route('/api/history', methods=['GET'])
def get_history():
    time_threshold = datetime.now() - timedelta(hours=24)
    results = list(collection.find(
        {"timestamp": {"$gte": time_threshold.strftime('%Y-%m-%d %H:%M:%S')}},
        {"timestamp": 1, "performance_results": 1, "gateway_ping_results": 1}
    ))
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)