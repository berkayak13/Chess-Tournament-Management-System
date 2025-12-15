#!/usr/bin/env python3
"""
Resource Monitoring Script for Performance Tests

This script monitors system resources (CPU, memory, network) during load tests.
Run alongside Locust tests to collect resource utilization metrics.

Usage:
    python monitor_resources.py --interval 1 --duration 300 --output test_results/resources.json

    Or with Docker container monitoring:
    python monitor_resources.py --container chess-tournament-app --interval 1
"""

import psutil
import time
import json
import argparse
import sys
import os
from datetime import datetime
from collections import defaultdict

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class ResourceMonitor:
    """Monitor system and application resources."""

    def __init__(self, interval=1, container_name=None):
        """
        Initialize resource monitor.

        Args:
            interval: Sampling interval in seconds
            container_name: Docker container name to monitor (optional)
        """
        self.interval = interval
        self.container_name = container_name
        self.docker_client = None
        self.container = None

        if container_name and DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                self.container = self.docker_client.containers.get(container_name)
            except Exception as e:
                print(f"Warning: Could not connect to Docker container '{container_name}': {e}")
                print("Falling back to system-wide monitoring")

        self.metrics = {
            'start_time': None,
            'end_time': None,
            'interval': interval,
            'samples': [],
            'summary': {}
        }

    def get_system_metrics(self):
        """Get current system-wide metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'per_cpu': psutil.cpu_percent(interval=0.1, percpu=True)
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'free': memory.free
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        }

    def get_container_metrics(self):
        """Get Docker container metrics."""
        if not self.container:
            return None

        try:
            stats = self.container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0 if system_delta > 0 else 0

            # Memory stats
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 1)
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0

            return {
                'timestamp': datetime.now().isoformat(),
                'container_name': self.container_name,
                'cpu_percent': cpu_percent,
                'memory': {
                    'usage': memory_usage,
                    'limit': memory_limit,
                    'percent': memory_percent,
                    'usage_mb': memory_usage / (1024 * 1024),
                    'limit_mb': memory_limit / (1024 * 1024)
                },
                'network': stats.get('networks', {}),
                'blkio': stats.get('blkio_stats', {})
            }
        except Exception as e:
            print(f"Error getting container stats: {e}")
            return None

    def collect_sample(self):
        """Collect one sample of metrics."""
        sample = {
            'system': self.get_system_metrics()
        }

        if self.container:
            container_metrics = self.get_container_metrics()
            if container_metrics:
                sample['container'] = container_metrics

        return sample

    def calculate_summary(self):
        """Calculate summary statistics from collected samples."""
        if not self.metrics['samples']:
            return {}

        # Extract values for statistical analysis
        cpu_values = [s['system']['cpu']['percent'] for s in self.metrics['samples']]
        memory_values = [s['system']['memory']['percent'] for s in self.metrics['samples']]

        summary = {
            'system': {
                'cpu': {
                    'min': min(cpu_values),
                    'max': max(cpu_values),
                    'avg': sum(cpu_values) / len(cpu_values),
                    'median': sorted(cpu_values)[len(cpu_values) // 2]
                },
                'memory': {
                    'min': min(memory_values),
                    'max': max(memory_values),
                    'avg': sum(memory_values) / len(memory_values),
                    'median': sorted(memory_values)[len(memory_values) // 2]
                }
            },
            'total_samples': len(self.metrics['samples']),
            'duration_seconds': (self.metrics['end_time'] - self.metrics['start_time']).total_seconds() if self.metrics['end_time'] else 0
        }

        # Container-specific summary
        if self.container and 'container' in self.metrics['samples'][0]:
            container_cpu = [s['container']['cpu_percent'] for s in self.metrics['samples'] if 'container' in s]
            container_mem = [s['container']['memory']['percent'] for s in self.metrics['samples'] if 'container' in s]

            if container_cpu and container_mem:
                summary['container'] = {
                    'name': self.container_name,
                    'cpu': {
                        'min': min(container_cpu),
                        'max': max(container_cpu),
                        'avg': sum(container_cpu) / len(container_cpu),
                        'median': sorted(container_cpu)[len(container_cpu) // 2]
                    },
                    'memory': {
                        'min': min(container_mem),
                        'max': max(container_mem),
                        'avg': sum(container_mem) / len(container_mem),
                        'median': sorted(container_mem)[len(container_mem) // 2]
                    }
                }

        return summary

    def monitor(self, duration=None):
        """
        Monitor resources for a specified duration or until interrupted.

        Args:
            duration: Duration in seconds, or None for infinite monitoring
        """
        self.metrics['start_time'] = datetime.now()
        print(f"Starting resource monitoring (interval: {self.interval}s)")
        if self.container:
            print(f"Monitoring Docker container: {self.container_name}")

        start_time = time.time()
        sample_count = 0

        try:
            while True:
                if duration and (time.time() - start_time) >= duration:
                    break

                sample = self.collect_sample()
                self.metrics['samples'].append(sample)
                sample_count += 1

                # Print live stats
                cpu = sample['system']['cpu']['percent']
                mem = sample['system']['memory']['percent']

                status = f"Sample {sample_count}: CPU: {cpu:.1f}% | Memory: {mem:.1f}%"

                if 'container' in sample and sample['container']:
                    cont_cpu = sample['container']['cpu_percent']
                    cont_mem = sample['container']['memory']['percent']
                    status += f" | Container CPU: {cont_cpu:.1f}% | Container Memory: {cont_mem:.1f}%"

                print(status)

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

        self.metrics['end_time'] = datetime.now()
        self.metrics['summary'] = self.calculate_summary()

        print(f"\nCollected {len(self.metrics['samples'])} samples")
        return self.metrics

    def save_results(self, output_file):
        """Save metrics to JSON file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Convert datetime objects to strings
        save_data = self.metrics.copy()
        if save_data['start_time']:
            save_data['start_time'] = save_data['start_time'].isoformat()
        if save_data['end_time']:
            save_data['end_time'] = save_data['end_time'].isoformat()

        with open(output_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        print(f"Results saved to {output_file}")

        # Print summary
        if self.metrics['summary']:
            print("\n" + "="*80)
            print("RESOURCE MONITORING SUMMARY")
            print("="*80)
            summary = self.metrics['summary']

            print(f"\nSystem Resources:")
            print(f"  CPU Usage:")
            print(f"    Average: {summary['system']['cpu']['avg']:.2f}%")
            print(f"    Min: {summary['system']['cpu']['min']:.2f}%")
            print(f"    Max: {summary['system']['cpu']['max']:.2f}%")

            print(f"\n  Memory Usage:")
            print(f"    Average: {summary['system']['memory']['avg']:.2f}%")
            print(f"    Min: {summary['system']['memory']['min']:.2f}%")
            print(f"    Max: {summary['system']['memory']['max']:.2f}%")

            if 'container' in summary:
                print(f"\nContainer '{self.container_name}':")
                print(f"  CPU Usage:")
                print(f"    Average: {summary['container']['cpu']['avg']:.2f}%")
                print(f"    Max: {summary['container']['cpu']['max']:.2f}%")

                print(f"\n  Memory Usage:")
                print(f"    Average: {summary['container']['memory']['avg']:.2f}%")
                print(f"    Max: {summary['container']['memory']['max']:.2f}%")

            print(f"\nDuration: {summary['duration_seconds']:.2f} seconds")
            print(f"Total Samples: {summary['total_samples']}")
            print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Monitor system resources during load tests')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Sampling interval in seconds (default: 1.0)')
    parser.add_argument('--duration', type=float, default=None,
                       help='Monitoring duration in seconds (default: until interrupted)')
    parser.add_argument('--container', type=str, default=None,
                       help='Docker container name to monitor')
    parser.add_argument('--output', type=str, default='test_results/resources.json',
                       help='Output file for results (default: test_results/resources.json)')

    args = parser.parse_args()

    if args.container and not DOCKER_AVAILABLE:
        print("Warning: docker package not installed. Cannot monitor container.")
        print("Install with: pip install docker")
        print("Continuing with system-wide monitoring only...")
        args.container = None

    monitor = ResourceMonitor(interval=args.interval, container_name=args.container)

    try:
        monitor.monitor(duration=args.duration)
        monitor.save_results(args.output)
    except Exception as e:
        print(f"Error during monitoring: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
