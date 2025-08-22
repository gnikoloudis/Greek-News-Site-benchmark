import json
import pandas as pd
from glob import glob
import os

def parse_log_file(log_data):
    """
    Parse a single log file (JSON string) and extract request load times and other metrics.
    Returns a list of dicts with URL, status, load time (ms), and encoded response length.
    """
    data = json.loads(log_data)
    entries = data.get('params', {})
    timestamp_map = {}
    request_start_map = {}
    requests = []

    for idx in range(len(data['method'])):
        method = data['method'][str(idx)] if str(idx) in data['method'] else data['method'][idx]
        params = entries[str(idx)] if str(idx) in entries else entries[idx]

        if method == 'Network.requestWillBeSent':
            request_id = params.get('requestId')
            request_start_map[request_id] = params

        elif method == 'Network.responseReceived':
            request_id = params.get('requestId')
            timestamp_map[request_id] = params

    for req_id, start_params in request_start_map.items():
        if req_id in timestamp_map:
            response_params = timestamp_map[req_id]
            try:
                start_time = start_params.get('timestamp', 0)
                response_time = response_params.get('timestamp', 0)
                load_time = (response_time - start_time) * 1000  # in milliseconds
                url = start_params.get('request', {}).get('url', '')
                status = response_params.get('response', {}).get('status', 0)
                encoded_length = response_params.get('response', {}).get('encodedDataLength', 0)

                requests.append({
                    'requestId': req_id,
                    'url': url,
                    'status': status,
                    'load_time_ms': load_time,
                    'encoded_length': encoded_length
                })
            except:
                continue

    return requests

def benchmark_sites(logs_dict):
    """
    Input: logs_dict = { 'site_name': log_file_content_as_string, ... }
    Output: Pandas DataFrame ranking sites by average load time
    """
    all_metrics = []
    for site_name, log_data in logs_dict.items():
        requests = parse_log_file(log_data)
        if not requests:
            continue
        df = pd.DataFrame(requests)
        avg_load = df['load_time_ms'].mean()
        median_load = df['load_time_ms'].median()
        p90_load = df['load_time_ms'].quantile(0.9)
        total_data = df['encoded_length'].sum()
        count_requests = len(df)

        all_metrics.append({
            'site': site_name,
            'average_load_ms': avg_load,
            'median_load_ms': median_load,
            'p90_load_ms': p90_load,
            'total_data_bytes': total_data,
            'request_count': count_requests
        })

    result_df = pd.DataFrame(all_metrics).sort_values('average_load_ms')
    return result_df


def load_logs_from_dir(dir_path, pattern='*.log'):
    """
    Loads all log files matching the glob pattern from the given directory,
    returning a dictionary mapping site names (basename without extension) to file contents.
    """
    logs_dict = {}
    files = glob("logs\*\*.log",recursive=True)
    for file_path in files:
        site_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as f:
            logs_dict[site_name] = f.read()
    return logs_dict


logs = load_logs_from_dir('logs/news_sites', '*.log')
result = benchmark_sites(logs)
result.to_csv('international_news_sites_benchmark_results.csv', index=False)
