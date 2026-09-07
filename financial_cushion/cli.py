"""CLI сервиса финансовой подушки.

Примеры:
    # базовый расчёт (нерешённые переводы попадут в блок уточнений)
    python -m financial_cushion.cli --pdf "выписка.pdf"

    # интерактивный режим: сервис спросит по каждому регулярному переводу
    python -m financial_cushion.cli --pdf "выписка.pdf" --interactive

    # решения по переводам из JSON-флага
    python -m financial_cushion.cli --pdf "выписка.pdf" \
        --decisions decisions.json --strategy mean

    # сгенерировать шаблон decisions.json по найденным кандидатам
    python -m financial_cushion.cli --pdf "выписка.pdf" --emit-template
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import calculate_cushion, prompt_decisions_interactive
from .reporting import build_report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="financial_cushion",
        description="Расчёт финансовой подушки по PDF-выписке Сбербанка",
    )
    parser.add_argument("--pdf", required=True, help="путь к PDF-выписке")
    parser.add_argument(
        "--decisions",
        help="JSON-флаг с решениями по регулярным переводам",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="спросить пользователя по каждому регулярному переводу",
    )
    parser.add_argument(
        "--strategy",
        choices=("mean", "median", "min"),
        default="mean",
        help=(
            "как считать сумму группы за месяц (по умолчанию mean — "
            "сумма за полные месяцы / число полных месяцев)"
        ),
    )
    parser.add_argument(
        "--min-month-share",
        type=float,
        default=0.5,
        help="доля полных месяцев для признания регулярности (по умолчанию 0.5)",
    )
    parser.add_argument(
        "--amount-tolerance",
        type=float,
        default=0.10,
        help="допустимый разброс сумм регулярных переводов (по умолчанию 0.10)",
    )
    parser.add_argument(
        "--emit-template",
        metavar="PATH",
        help="записать шаблон decisions.json по найденным кандидатам и выйти",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    result = calculate_cushion(
        args.pdf,
        decisions=args.decisions,
        strategy=args.strategy,
        min_month_share=args.min_month_share,
        amount_tolerance=args.amount_tolerance,
    )

    if args.emit_template:
        template = {
            c.counterparty: {"label": "", "include": False}
            for c in result.pending_candidates
        }
        Path(args.emit_template).write_text(
            json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Шаблон решений записан: {args.emit_template}")
        return 0

    if args.interactive:
        prompt_decisions_interactive(result.pending_candidates)
        # Пересчитываем итог с учётом подтверждённых переводов
        result = calculate_cushion(
            args.pdf,
            decisions={
                c.counterparty: {"include": c.include, "label": c.label}
                for c in result.candidates
            },
            strategy=args.strategy,
            min_month_share=args.min_month_share,
            amount_tolerance=args.amount_tolerance,
        )

    print(build_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
