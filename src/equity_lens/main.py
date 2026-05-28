#!/usr/bin/env python
import argparse
import warnings
from datetime import datetime

from dotenv import load_dotenv

from equity_lens.crew import EquityLens

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def parse_args():
    p = argparse.ArgumentParser(
        description="Equity Lens — AI-powered investment research pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  equity_lens --universe "Semiconductors" --geography "US"
  equity_lens --universe "Fintech" --geography "Europe" --strategy growth
  equity_lens --universe "Cloud Computing" --geography "global" --min-size 5000000000
  equity_lens --universe "AI Infrastructure" --strategy growth --horizon 12
        """
    )
    p.add_argument(
        "--universe",
        default="Technology",
        help="Investment universe to research, e.g. 'Semiconductors', 'Fintech' (default: Technology)"
    )
    p.add_argument(
        "--geography",
        default="global",
        choices=["global", "US", "Europe", "Asia"],
        help="Geographic focus (default: global)"
    )
    p.add_argument(
        "--strategy",
        default="balanced",
        choices=["value", "growth", "balanced"],
        help="Investment strategy determining scoring weights (default: balanced)"
    )
    p.add_argument(
        "--horizon",
        type=int,
        default=12,
        help="Investment holding horizon in months (default: 12)"
    )
    p.add_argument(
        "--min-size",
        type=int,
        default=2_000_000_000,
        help="Minimum market cap in USD (default: 2000000000)"
    )
    p.add_argument(
        "--date",
        default=None,
        help="Override current date for testing, format: 'May 24 2026'"
    )
    return p.parse_args()


def run():
    load_dotenv()
    args = parse_args()

    current_date = (
        args.date if args.date
        else datetime.now().strftime("%B %d, %Y")
    )

    inputs = {
        "universe": args.universe,
        "geography": args.geography,
        "strategy": args.strategy,
        "horizon": args.horizon,
        "min_size": args.min_size,
        "current_date": current_date,
    }

    print("\n" + "=" * 60)
    print("  EQUITY LENS — Investment Research Pipeline")
    print("=" * 60)
    print(f"  Universe:   {args.universe}")
    print(f"  Geography:  {args.geography}")
    print(f"  Strategy:   {args.strategy}")
    print(f"  Horizon:    {args.horizon} months")
    print(f"  Min Size:   ${args.min_size:,.0f}")
    print(f"  Date:       {current_date}")
    print("=" * 60 + "\n")

    result = EquityLens().crew().kickoff(inputs=inputs)

    print("\n" + "=" * 60)
    print("  FINAL RECOMMENDATION")
    print("=" * 60 + "\n")
    print(result.raw)


if __name__ == "__main__":
    run()