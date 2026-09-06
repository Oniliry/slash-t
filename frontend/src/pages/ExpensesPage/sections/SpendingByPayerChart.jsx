import "./SpendingByPayerChart.css";

const COLORS = ["#21a038", "#2f6fed", "#8854d0", "#177a2b", "#5ec9c9", "#8a969f"];

const currencyFormatter = new Intl.NumberFormat("ru-RU", {
  maximumFractionDigits: 0,
});

function formatAmount(value) {
  return `${currencyFormatter.format(value)} ₽`;
}

function buildSlices(entries, total) {
  const circumference = 2 * Math.PI * 45;
  let offset = 0;

  return entries.map((entry, index) => {
    const share = total > 0 ? entry.total / total : 0;
    const length = share * circumference;
    const slice = {
      ...entry,
      color: COLORS[index % COLORS.length],
      share,
      dasharray: `${length} ${circumference - length}`,
      dashoffset: -offset,
    };
    offset += length;
    return slice;
  });
}

// Считает, кому реально принадлежит каждая покупка, а не кто её физически оплатил:
// - "self" (личный расход) — вся сумма на плательщике;
// - "member" (покупка другого участника) — вся сумма на этом участнике;
// - "shared" (общая) — сумма делится между всеми взрослыми участниками
//   пропорционально их доле бюджета (income_share), точно так же, как считаются долги.
function buildMemberTotals(expenses, members) {
  const membersById = new Map(members.map((member) => [member.id, member]));
  const totals = new Map();

  function addAmount(memberId, amount) {
    if (!memberId || !amount) return;

    const existing = totals.get(memberId);
    if (existing) {
      existing.total += amount;
      return;
    }

    totals.set(memberId, {
      id: memberId,
      name: membersById.get(memberId)?.name ?? "Участник",
      total: amount,
    });
  }

  expenses.forEach((expense) => {
    const amount = Number(expense.amount);

    if (expense.owner_type === "member") {
      addAmount(expense.owner_id, amount);
      return;
    }

    if (expense.owner_type === "shared") {
      members.forEach((member) => {
        if (!member.income_share) return;
        addAmount(member.id, amount * member.income_share);
      });
      return;
    }

    // owner_type === "self" — личный расход, вся сумма на плательщике.
    addAmount(expense.payer_id, amount);
  });

  return totals;
}

function SpendingByPayerChart({ expenses, members = [] }) {
  const totalsByMember = buildMemberTotals(expenses, members);

  const entries = [...totalsByMember.values()].sort((a, b) => b.total - a.total);
  const total = entries.reduce((sum, entry) => sum + entry.total, 0);

  if (entries.length === 0) {
    return null;
  }

  const slices = buildSlices(entries, total);

  return (
    <div className="spending-chart">
      <svg className="spending-chart__donut" viewBox="0 0 120 120" role="img" aria-label="Кому принадлежат траты">
        <circle className="spending-chart__track" cx="60" cy="60" r="45" />
        {slices.map((slice) => (
          <circle
            key={slice.id}
            cx="60"
            cy="60"
            r="45"
            stroke={slice.color}
            strokeWidth="16"
            fill="none"
            strokeDasharray={slice.dasharray}
            strokeDashoffset={slice.dashoffset}
            transform="rotate(-90 60 60)"
          />
        ))}
      </svg>

      <ul className="spending-chart__legend">
        {slices.map((slice) => (
          <li className="spending-chart__legend-item" key={slice.id}>
            <span
              className="spending-chart__dot"
              style={{ background: slice.color }}
              aria-hidden="true"
            />
            <span className="spending-chart__legend-name">{slice.name}</span>
            <span className="spending-chart__legend-value">
              {formatAmount(slice.total)} · {Math.round(slice.share * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SpendingByPayerChart;
