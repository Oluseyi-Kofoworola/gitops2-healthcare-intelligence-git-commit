#!/usr/bin/env python3
"""
AI Cost Tracker - OpenAI API Usage Monitoring and Budget Alerts

Tracks OpenAI API usage, enforces rate limits, and sends budget alerts.
Prevents cost overruns by monitoring token usage and API calls per user/team.

Usage:
    python tools/ai_cost_tracker.py --log-usage --user john.doe --tokens 1500
    python tools/ai_cost_tracker.py --check-budget
    python tools/ai_cost_tracker.py --user-stats john.doe
    python tools/ai_cost_tracker.py --report monthly
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pricing (as of Dec 2024 - update regularly)
PRICING = {
    'gpt-4': {
        'input': 0.03 / 1000,    # $0.03 per 1K input tokens
        'output': 0.06 / 1000,   # $0.06 per 1K output tokens
    },
    'gpt-4-turbo': {
        'input': 0.01 / 1000,
        'output': 0.03 / 1000,
    },
    'gpt-3.5-turbo': {
        'input': 0.0015 / 1000,
        'output': 0.002 / 1000,
    },
    'o1-preview': {
        'input': 0.015 / 1000,
        'output': 0.06 / 1000,
    },
    'o1-mini': {
        'input': 0.003 / 1000,
        'output': 0.012 / 1000,
    },
}

# Budget thresholds
MONTHLY_BUDGET_LIMIT = 5000.00  # $5K/month
DAILY_BUDGET_LIMIT = 200.00      # $200/day
USER_DAILY_LIMIT = 50.00         # $50 per user per day
TEAM_DAILY_LIMIT = 150.00        # $150 per team per day

# Rate limits
USER_HOURLY_TOKEN_LIMIT = 100000    # 100K tokens/hour per user
TEAM_HOURLY_TOKEN_LIMIT = 500000    # 500K tokens/hour per team


class CostTracker:
    """Tracks OpenAI API costs and enforces budget limits."""
    
    def __init__(self, data_dir: str = ".ai_cost_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.usage_file = self.data_dir / "usage.jsonl"
        self.budget_file = self.data_dir / "budget_alerts.json"
        self.rate_limit_file = self.data_dir / "rate_limits.json"
    
    def log_usage(
        self,
        user: str,
        team: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "commit_generation"
    ) -> Dict:
        """
        Log API usage and calculate cost.
        
        Args:
            user: Username or email
            team: Team identifier
            model: OpenAI model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Type of operation (e.g., "commit_generation")
        
        Returns:
            Dict with usage details and cost
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Calculate cost
        pricing = PRICING.get(model, PRICING['gpt-4-turbo'])
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        total_cost = input_cost + output_cost
        
        usage_record = {
            'timestamp': timestamp,
            'user': user,
            'team': team,
            'model': model,
            'operation': operation,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(total_cost, 6),
        }
        
        # Append to usage log
        with open(self.usage_file, 'a') as f:
            f.write(json.dumps(usage_record) + '\n')
        
        logger.info(f"Logged usage: {user} - {model} - ${total_cost:.4f}")
        
        # Check if budget alert needed
        self._check_budget_alerts(user, team, total_cost)
        
        return usage_record
    
    def _check_budget_alerts(self, user: str, team: str, new_cost: float):
        """Check if budget thresholds are exceeded and send alerts."""
        today = datetime.utcnow().date()
        
        # Get today's spending
        daily_totals = self._get_daily_totals(today)
        user_daily = daily_totals['users'].get(user, 0.0) + new_cost
        team_daily = daily_totals['teams'].get(team, 0.0) + new_cost
        overall_daily = daily_totals['overall'] + new_cost
        
        # Get monthly spending
        monthly_total = self._get_monthly_total() + new_cost
        
        alerts = []
        
        # Check thresholds
        if user_daily > USER_DAILY_LIMIT:
            alert = {
                'type': 'USER_DAILY_LIMIT_EXCEEDED',
                'user': user,
                'limit': USER_DAILY_LIMIT,
                'current': user_daily,
                'severity': 'HIGH',
                'message': f"User {user} exceeded daily limit: ${user_daily:.2f}/${USER_DAILY_LIMIT:.2f}"
            }
            alerts.append(alert)
            logger.warning(alert['message'])
        
        if team_daily > TEAM_DAILY_LIMIT:
            alert = {
                'type': 'TEAM_DAILY_LIMIT_EXCEEDED',
                'team': team,
                'limit': TEAM_DAILY_LIMIT,
                'current': team_daily,
                'severity': 'HIGH',
                'message': f"Team {team} exceeded daily limit: ${team_daily:.2f}/${TEAM_DAILY_LIMIT:.2f}"
            }
            alerts.append(alert)
            logger.warning(alert['message'])
        
        if overall_daily > DAILY_BUDGET_LIMIT:
            alert = {
                'type': 'DAILY_BUDGET_EXCEEDED',
                'limit': DAILY_BUDGET_LIMIT,
                'current': overall_daily,
                'severity': 'CRITICAL',
                'message': f"Daily budget exceeded: ${overall_daily:.2f}/${DAILY_BUDGET_LIMIT:.2f}"
            }
            alerts.append(alert)
            logger.error(alert['message'])
        
        if monthly_total > MONTHLY_BUDGET_LIMIT:
            alert = {
                'type': 'MONTHLY_BUDGET_EXCEEDED',
                'limit': MONTHLY_BUDGET_LIMIT,
                'current': monthly_total,
                'severity': 'CRITICAL',
                'message': f"Monthly budget exceeded: ${monthly_total:.2f}/${MONTHLY_BUDGET_LIMIT:.2f}"
            }
            alerts.append(alert)
            logger.error(alert['message'])
        
        # Save alerts
        if alerts:
            self._save_alerts(alerts)
    
    def check_rate_limit(self, user: str, team: str, tokens: int) -> Tuple[bool, str]:
        """
        Check if user/team is within rate limits.
        
        Returns:
            Tuple of (allowed: bool, message: str)
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Load rate limit tracking
        rate_limits = self._load_rate_limits()
        
        # Clean old entries
        rate_limits = {
            k: [entry for entry in v if datetime.fromisoformat(entry['timestamp']) > hour_ago]
            for k, v in rate_limits.items()
        }
        
        # Calculate current usage
        user_tokens = sum(entry['tokens'] for entry in rate_limits.get(f'user:{user}', []))
        team_tokens = sum(entry['tokens'] for entry in rate_limits.get(f'team:{team}', []))
        
        # Check limits
        if user_tokens + tokens > USER_HOURLY_TOKEN_LIMIT:
            return False, f"User rate limit exceeded: {user_tokens}/{USER_HOURLY_TOKEN_LIMIT} tokens/hour"
        
        if team_tokens + tokens > TEAM_HOURLY_TOKEN_LIMIT:
            return False, f"Team rate limit exceeded: {team_tokens}/{TEAM_HOURLY_TOKEN_LIMIT} tokens/hour"
        
        # Log this request
        rate_limits.setdefault(f'user:{user}', []).append({
            'timestamp': now.isoformat(),
            'tokens': tokens
        })
        rate_limits.setdefault(f'team:{team}', []).append({
            'timestamp': now.isoformat(),
            'tokens': tokens
        })
        
        self._save_rate_limits(rate_limits)
        
        return True, "Within rate limits"
    
    def _get_daily_totals(self, date) -> Dict:
        """Get spending totals for a specific date."""
        totals = {'users': {}, 'teams': {}, 'overall': 0.0}
        
        if not self.usage_file.exists():
            return totals
        
        date_str = date.isoformat()
        
        with open(self.usage_file, 'r') as f:
            for line in f:
                record = json.loads(line)
                record_date = record['timestamp'][:10]
                
                if record_date == date_str:
                    cost = record['total_cost']
                    user = record['user']
                    team = record['team']
                    
                    totals['users'][user] = totals['users'].get(user, 0.0) + cost
                    totals['teams'][team] = totals['teams'].get(team, 0.0) + cost
                    totals['overall'] += cost
        
        return totals
    
    def _get_monthly_total(self) -> float:
        """Get total spending for current month."""
        if not self.usage_file.exists():
            return 0.0
        
        now = datetime.utcnow()
        month_str = now.strftime('%Y-%m')
        total = 0.0
        
        with open(self.usage_file, 'r') as f:
            for line in f:
                record = json.loads(line)
                record_month = record['timestamp'][:7]
                
                if record_month == month_str:
                    total += record['total_cost']
        
        return total
    
    def get_user_stats(self, user: str, days: int = 30) -> Dict:
        """Get usage statistics for a user."""
        if not self.usage_file.exists():
            return {'total_cost': 0.0, 'total_tokens': 0, 'calls': 0}
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        stats = {
            'user': user,
            'period_days': days,
            'total_cost': 0.0,
            'total_tokens': 0,
            'calls': 0,
            'by_model': {},
            'by_operation': {},
        }
        
        with open(self.usage_file, 'r') as f:
            for line in f:
                record = json.loads(line)
                
                if record['user'] == user and record['timestamp'] >= cutoff_str:
                    stats['total_cost'] += record['total_cost']
                    stats['total_tokens'] += record['total_tokens']
                    stats['calls'] += 1
                    
                    model = record['model']
                    stats['by_model'][model] = stats['by_model'].get(model, 0.0) + record['total_cost']
                    
                    op = record['operation']
                    stats['by_operation'][op] = stats['by_operation'].get(op, 0.0) + record['total_cost']
        
        return stats
    
    def generate_report(self, period: str = 'daily') -> Dict:
        """Generate usage report."""
        if period == 'daily':
            date = datetime.utcnow().date()
            totals = self._get_daily_totals(date)
            return {
                'period': 'daily',
                'date': date.isoformat(),
                'total_cost': totals['overall'],
                'budget_limit': DAILY_BUDGET_LIMIT,
                'usage_percent': (totals['overall'] / DAILY_BUDGET_LIMIT * 100),
                'by_user': totals['users'],
                'by_team': totals['teams'],
            }
        elif period == 'monthly':
            total = self._get_monthly_total()
            return {
                'period': 'monthly',
                'month': datetime.utcnow().strftime('%Y-%m'),
                'total_cost': total,
                'budget_limit': MONTHLY_BUDGET_LIMIT,
                'usage_percent': (total / MONTHLY_BUDGET_LIMIT * 100),
            }
        else:
            raise ValueError(f"Invalid period: {period}")
    
    def _load_rate_limits(self) -> Dict:
        """Load rate limit tracking data."""
        if not self.rate_limit_file.exists():
            return {}
        
        with open(self.rate_limit_file, 'r') as f:
            return json.load(f)
    
    def _save_rate_limits(self, rate_limits: Dict):
        """Save rate limit tracking data."""
        with open(self.rate_limit_file, 'w') as f:
            json.dump(rate_limits, f, indent=2)
    
    def _save_alerts(self, alerts: List[Dict]):
        """Save budget alerts."""
        existing_alerts = []
        if self.budget_file.exists():
            with open(self.budget_file, 'r') as f:
                existing_alerts = json.load(f)
        
        for alert in alerts:
            alert['timestamp'] = datetime.utcnow().isoformat()
        
        existing_alerts.extend(alerts)
        
        with open(self.budget_file, 'w') as f:
            json.dump(existing_alerts, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='AI Cost Tracker - Monitor OpenAI API usage')
    
    parser.add_argument('--log-usage', action='store_true', help='Log API usage')
    parser.add_argument('--user', type=str, help='Username or email')
    parser.add_argument('--team', type=str, default='default', help='Team identifier')
    parser.add_argument('--model', type=str, default='gpt-4-turbo', help='OpenAI model')
    parser.add_argument('--input-tokens', type=int, dest='input_tokens', help='Input tokens')
    parser.add_argument('--output-tokens', type=int, dest='output_tokens', help='Output tokens')
    parser.add_argument('--tokens', type=int, help='Total tokens (splits 60/40 input/output)')
    parser.add_argument('--operation', type=str, default='commit_generation', help='Operation type')
    
    parser.add_argument('--check-rate-limit', action='store_true', help='Check rate limits')
    parser.add_argument('--user-stats', type=str, help='Get user statistics')
    parser.add_argument('--days', type=int, default=30, help='Days for statistics')
    parser.add_argument('--report', type=str, choices=['daily', 'monthly'], help='Generate report')
    parser.add_argument('--check-budget', action='store_true', help='Check current budget status')
    
    args = parser.parse_args()
    
    tracker = CostTracker()
    
    if args.log_usage:
        if not args.user:
            print("Error: --user required for --log-usage")
            sys.exit(1)
        
        if args.tokens:
            # Split tokens 60/40 input/output (typical ratio)
            input_tokens = int(args.tokens * 0.6)
            output_tokens = int(args.tokens * 0.4)
        elif args.input_tokens and args.output_tokens:
            input_tokens = args.input_tokens
            output_tokens = args.output_tokens
        else:
            print("Error: Either --tokens or both --input-tokens and --output-tokens required")
            sys.exit(1)
        
        result = tracker.log_usage(
            user=args.user,
            team=args.team,
            model=args.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            operation=args.operation
        )
        
        print(json.dumps(result, indent=2))
    
    elif args.check_rate_limit:
        if not args.user or not args.tokens:
            print("Error: --user and --tokens required for --check-rate-limit")
            sys.exit(1)
        
        allowed, message = tracker.check_rate_limit(args.user, args.team, args.tokens)
        
        if allowed:
            print(f"✅ {message}")
            sys.exit(0)
        else:
            print(f"❌ {message}")
            sys.exit(1)
    
    elif args.user_stats:
        stats = tracker.get_user_stats(args.user_stats, args.days)
        print(json.dumps(stats, indent=2))
    
    elif args.report:
        report = tracker.generate_report(args.report)
        print(json.dumps(report, indent=2))
    
    elif args.check_budget:
        daily_report = tracker.generate_report('daily')
        monthly_report = tracker.generate_report('monthly')
        
        print("\n" + "="*60)
        print("BUDGET STATUS REPORT")
        print("="*60)
        
        print(f"\n📅 Daily Budget (Today):")
        print(f"   Spent: ${daily_report['total_cost']:.2f}")
        print(f"   Limit: ${daily_report['budget_limit']:.2f}")
        print(f"   Usage: {daily_report['usage_percent']:.1f}%")
        
        if daily_report['usage_percent'] > 80:
            print("   ⚠️  WARNING: Over 80% of daily budget")
        
        print(f"\n📅 Monthly Budget ({monthly_report['month']}):")
        print(f"   Spent: ${monthly_report['total_cost']:.2f}")
        print(f"   Limit: ${monthly_report['budget_limit']:.2f}")
        print(f"   Usage: {monthly_report['usage_percent']:.1f}%")
        
        if monthly_report['usage_percent'] > 80:
            print("   ⚠️  WARNING: Over 80% of monthly budget")
        
        print("\n" + "="*60)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
