#!/usr/bin/env python3
"""
Performance Test Results Analyzer

This script analyzes load test results and generates:
- Statistical analysis
- Performance insights
- Comparison between test runs
- Visualization-ready data for slides

Usage:
    python analyze_results.py
    python analyze_results.py --results test_results/performance_results_*.json
    python analyze_results.py --compare test1.json test2.json
"""

import json
import glob
import argparse
import os
from datetime import datetime
from pathlib import Path
import statistics


class PerformanceAnalyzer:
    """Analyze performance test results."""

    def __init__(self):
        self.results = []
        self.resource_data = []

    def load_results(self, pattern='test_results/performance_results_*.json'):
        """Load all performance result files matching pattern."""
        files = glob.glob(pattern)

        if not files:
            print(f"No result files found matching: {pattern}")
            return

        for file_path in sorted(files):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    data['_file'] = file_path
                    self.results.append(data)
                print(f"Loaded: {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        print(f"\nLoaded {len(self.results)} result file(s)")

    def load_resource_data(self, pattern='test_results/resources_*.json'):
        """Load resource monitoring data."""
        files = glob.glob(pattern)

        for file_path in sorted(files):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    data['_file'] = file_path
                    self.resource_data.append(data)
                print(f"Loaded resource data: {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    def analyze_single_test(self, result):
        """Analyze a single test result."""
        print("\n" + "="*80)
        print(f"ANALYSIS: {result['_file']}")
        print("="*80)

        info = result['test_info']
        stats = result['overall_stats']
        percentiles = result['percentiles']

        print(f"\nTest Information:")
        print(f"  Start Time: {info['start_time']}")
        print(f"  Duration: {info['duration_seconds']:.2f} seconds")
        print(f"  Target Host: {info['host']}")

        print(f"\nOverall Performance:")
        print(f"  Total Requests: {stats['total_requests']:,}")
        print(f"  Total Failures: {stats['total_failures']:,}")
        print(f"  Failure Rate: {stats['failure_rate']*100:.2f}%")
        print(f"  Throughput: {stats['requests_per_second']:.2f} req/s")

        print(f"\nResponse Time Statistics:")
        print(f"  Average: {stats['average_response_time']:.2f} ms")
        print(f"  Minimum: {stats['min_response_time']:.2f} ms")
        print(f"  Maximum: {stats['max_response_time']:.2f} ms")
        print(f"  Median (p50): {percentiles['p50']:.2f} ms")
        print(f"  p95: {percentiles['p95']:.2f} ms")
        print(f"  p99: {percentiles['p99']:.2f} ms")

        # Performance assessment
        print(f"\nPerformance Assessment:")
        self._assess_performance(stats, percentiles)

        # Endpoint analysis
        print(f"\nTop 5 Slowest Endpoints:")
        endpoints = result.get('endpoint_details', {})
        sorted_endpoints = sorted(
            endpoints.items(),
            key=lambda x: x[1]['avg_response_time'],
            reverse=True
        )[:5]

        for i, (name, ep_stats) in enumerate(sorted_endpoints, 1):
            print(f"  {i}. {name}")
            print(f"     Avg: {ep_stats['avg_response_time']:.2f} ms | "
                  f"p95: {ep_stats['percentiles']['p95']:.2f} ms | "
                  f"Requests: {ep_stats['num_requests']:,} | "
                  f"Failures: {ep_stats['num_failures']:,}")

        # Most requested endpoints
        print(f"\nTop 5 Most Requested Endpoints:")
        sorted_by_requests = sorted(
            endpoints.items(),
            key=lambda x: x[1]['num_requests'],
            reverse=True
        )[:5]

        for i, (name, ep_stats) in enumerate(sorted_by_requests, 1):
            print(f"  {i}. {name}")
            print(f"     Requests: {ep_stats['num_requests']:,} | "
                  f"RPS: {ep_stats['requests_per_second']:.2f} | "
                  f"Avg RT: {ep_stats['avg_response_time']:.2f} ms")

    def _assess_performance(self, stats, percentiles):
        """Provide performance assessment based on metrics."""
        issues = []
        recommendations = []

        # Check failure rate
        if stats['failure_rate'] > 0.05:  # > 5%
            issues.append(f"⚠ High failure rate: {stats['failure_rate']*100:.2f}%")
            recommendations.append("Investigate error logs and increase server capacity")
        elif stats['failure_rate'] > 0.01:  # > 1%
            issues.append(f"⚠ Moderate failure rate: {stats['failure_rate']*100:.2f}%")
        else:
            print(f"  ✓ Excellent failure rate: {stats['failure_rate']*100:.2f}%")

        # Check response times
        if percentiles['p95'] > 2000:  # > 2 seconds
            issues.append(f"⚠ High p95 response time: {percentiles['p95']:.2f} ms")
            recommendations.append("Optimize slow endpoints or add caching")
        elif percentiles['p95'] > 1000:  # > 1 second
            issues.append(f"⚠ Moderate p95 response time: {percentiles['p95']:.2f} ms")
        else:
            print(f"  ✓ Good p95 response time: {percentiles['p95']:.2f} ms")

        # Check p99
        if percentiles['p99'] > 5000:  # > 5 seconds
            issues.append(f"⚠ Very high p99 response time: {percentiles['p99']:.2f} ms")
            recommendations.append("Investigate outliers and database query performance")
        elif percentiles['p99'] > 3000:  # > 3 seconds
            issues.append(f"⚠ High p99 response time: {percentiles['p99']:.2f} ms")

        # Check throughput
        if stats['requests_per_second'] < 10:
            issues.append(f"⚠ Low throughput: {stats['requests_per_second']:.2f} req/s")
            recommendations.append("Consider horizontal scaling or performance optimization")
        else:
            print(f"  ✓ Throughput: {stats['requests_per_second']:.2f} req/s")

        # Print issues and recommendations
        if issues:
            print("\n  Issues Identified:")
            for issue in issues:
                print(f"    {issue}")

        if recommendations:
            print("\n  Recommendations:")
            for rec in recommendations:
                print(f"    • {rec}")

    def compare_tests(self, file1, file2):
        """Compare two test results."""
        with open(file1, 'r') as f:
            result1 = json.load(f)
        with open(file2, 'r') as f:
            result2 = json.load(f)

        print("\n" + "="*80)
        print("TEST COMPARISON")
        print("="*80)
        print(f"\nTest 1: {file1}")
        print(f"Test 2: {file2}")

        stats1 = result1['overall_stats']
        stats2 = result2['overall_stats']

        metrics = [
            ('Total Requests', 'total_requests', ''),
            ('Failure Rate', 'failure_rate', '%'),
            ('Throughput', 'requests_per_second', 'req/s'),
            ('Avg Response Time', 'average_response_time', 'ms'),
            ('p95 Response Time', 'p95', 'ms'),
            ('p99 Response Time', 'p99', 'ms'),
        ]

        print(f"\n{'Metric':<25} {'Test 1':<15} {'Test 2':<15} {'Change':<15}")
        print("-" * 70)

        for name, key, unit in metrics:
            if key.startswith('p'):
                val1 = result1['percentiles'][key]
                val2 = result2['percentiles'][key]
            else:
                val1 = stats1[key]
                val2 = stats2[key]

            if key == 'failure_rate':
                val1 *= 100
                val2 *= 100

            change = ((val2 - val1) / val1 * 100) if val1 > 0 else 0
            change_str = f"{change:+.1f}%"

            if 'response_time' in key.lower() or key.startswith('p'):
                # For response times, lower is better
                indicator = "↓" if change < 0 else "↑"
            else:
                # For throughput, higher is better
                indicator = "↑" if change > 0 else "↓"

            print(f"{name:<25} {val1:<15.2f} {val2:<15.2f} {indicator} {change_str}")

    def analyze_resources(self, resource_file):
        """Analyze resource monitoring data."""
        with open(resource_file, 'r') as f:
            data = json.load(f)

        print("\n" + "="*80)
        print(f"RESOURCE USAGE ANALYSIS: {resource_file}")
        print("="*80)

        summary = data.get('summary', {})

        if 'system' in summary:
            sys_cpu = summary['system']['cpu']
            sys_mem = summary['system']['memory']

            print(f"\nSystem Resources:")
            print(f"  CPU Usage:")
            print(f"    Average: {sys_cpu['avg']:.2f}%")
            print(f"    Peak: {sys_cpu['max']:.2f}%")
            print(f"    Minimum: {sys_cpu['min']:.2f}%")

            print(f"\n  Memory Usage:")
            print(f"    Average: {sys_mem['avg']:.2f}%")
            print(f"    Peak: {sys_mem['max']:.2f}%")
            print(f"    Minimum: {sys_mem['min']:.2f}%")

            # Resource assessment
            print(f"\n  Resource Assessment:")
            if sys_cpu['avg'] > 80:
                print(f"    ⚠ High CPU usage detected - consider scaling")
            elif sys_cpu['avg'] > 60:
                print(f"    ⚠ Moderate CPU usage - monitor closely")
            else:
                print(f"    ✓ CPU usage is healthy")

            if sys_mem['avg'] > 80:
                print(f"    ⚠ High memory usage detected - check for memory leaks")
            elif sys_mem['avg'] > 60:
                print(f"    ⚠ Moderate memory usage - monitor closely")
            else:
                print(f"    ✓ Memory usage is healthy")

        if 'container' in summary:
            cont = summary['container']
            print(f"\n  Container '{cont['name']}':")
            print(f"    CPU Average: {cont['cpu']['avg']:.2f}%")
            print(f"    CPU Peak: {cont['cpu']['max']:.2f}%")
            print(f"    Memory Average: {cont['memory']['avg']:.2f}%")
            print(f"    Memory Peak: {cont['memory']['max']:.2f}%")

        print(f"\n  Duration: {summary.get('duration_seconds', 0):.2f} seconds")
        print(f"  Samples: {summary.get('total_samples', 0):,}")

    def generate_summary_report(self, output_file='test_results/summary_report.txt'):
        """Generate a comprehensive summary report."""
        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("PERFORMANCE TESTING SUMMARY REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Tests Analyzed: {len(self.results)}\n\n")

            for i, result in enumerate(self.results, 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"Test {i}: {Path(result['_file']).name}\n")
                f.write(f"{'='*80}\n\n")

                info = result['test_info']
                stats = result['overall_stats']
                percentiles = result['percentiles']

                f.write(f"Duration: {info['duration_seconds']:.2f}s\n")
                f.write(f"Total Requests: {stats['total_requests']:,}\n")
                f.write(f"Failure Rate: {stats['failure_rate']*100:.2f}%\n")
                f.write(f"Throughput: {stats['requests_per_second']:.2f} req/s\n")
                f.write(f"Avg Response Time: {stats['average_response_time']:.2f} ms\n")
                f.write(f"p95: {percentiles['p95']:.2f} ms\n")
                f.write(f"p99: {percentiles['p99']:.2f} ms\n")

        print(f"\nSummary report saved to: {output_file}")

    def generate_slide_data(self, output_file='test_results/slide_data.json'):
        """Generate data formatted for presentation slides."""
        slide_data = {
            'generated_at': datetime.now().isoformat(),
            'test_summary': [],
            'key_metrics': {},
            'charts': {}
        }

        # Aggregate metrics
        if self.results:
            all_throughput = [r['overall_stats']['requests_per_second'] for r in self.results]
            all_p95 = [r['percentiles']['p95'] for r in self.results]
            all_failures = [r['overall_stats']['failure_rate'] for r in self.results]

            slide_data['key_metrics'] = {
                'avg_throughput': statistics.mean(all_throughput),
                'max_throughput': max(all_throughput),
                'avg_p95': statistics.mean(all_p95),
                'avg_failure_rate': statistics.mean(all_failures),
                'total_requests': sum(r['overall_stats']['total_requests'] for r in self.results)
            }

            # Per-test summary
            for result in self.results:
                test_name = Path(result['_file']).stem
                slide_data['test_summary'].append({
                    'name': test_name,
                    'throughput': result['overall_stats']['requests_per_second'],
                    'p95': result['percentiles']['p95'],
                    'p99': result['percentiles']['p99'],
                    'failure_rate': result['overall_stats']['failure_rate'],
                    'total_requests': result['overall_stats']['total_requests']
                })

        with open(output_file, 'w') as f:
            json.dump(slide_data, f, indent=2)

        print(f"Slide data saved to: {output_file}")

    def print_test_summary_table(self):
        """Print a comparison table of all tests."""
        if not self.results:
            print("No results loaded")
            return

        print("\n" + "="*80)
        print("ALL TESTS SUMMARY")
        print("="*80 + "\n")

        # Header
        print(f"{'Test':<30} {'Requests':<12} {'RPS':<10} {'p95 (ms)':<12} {'Fail %':<10}")
        print("-" * 80)

        for result in self.results:
            test_name = Path(result['_file']).stem.replace('performance_results_', '')
            stats = result['overall_stats']
            percentiles = result['percentiles']

            print(f"{test_name:<30} "
                  f"{stats['total_requests']:<12,} "
                  f"{stats['requests_per_second']:<10.2f} "
                  f"{percentiles['p95']:<12.2f} "
                  f"{stats['failure_rate']*100:<10.2f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Analyze performance test results')
    parser.add_argument('--results', type=str, default='test_results/performance_results_*.json',
                       help='Pattern for performance result files')
    parser.add_argument('--resources', type=str, default='test_results/resources_*.json',
                       help='Pattern for resource monitoring files')
    parser.add_argument('--compare', nargs=2, metavar=('FILE1', 'FILE2'),
                       help='Compare two test result files')
    parser.add_argument('--summary', action='store_true',
                       help='Generate summary report')

    args = parser.parse_args()

    analyzer = PerformanceAnalyzer()

    if args.compare:
        analyzer.compare_tests(args.compare[0], args.compare[1])
    else:
        # Load and analyze all results
        analyzer.load_results(args.results)

        if analyzer.results:
            # Analyze each test
            for result in analyzer.results:
                analyzer.analyze_single_test(result)

            # Print summary table
            analyzer.print_test_summary_table()

            # Generate outputs
            analyzer.generate_summary_report()
            analyzer.generate_slide_data()

        # Load and analyze resource data
        analyzer.load_resource_data(args.resources)
        for resource_file in glob.glob(args.resources):
            analyzer.analyze_resources(resource_file)


if __name__ == '__main__':
    main()
