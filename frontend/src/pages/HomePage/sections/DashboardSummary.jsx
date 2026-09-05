import './DashboardSummary.css'

function DashboardSummary() {
  return (
    <div className="stats-grid">
      <article className="card"><span className="card__eyebrow">Бюджет семьи</span><strong className="stat__value">75 000 ₽</strong><span className="stat__caption">на текущий месяц</span></article>
      <article className="card"><span className="card__eyebrow">Общие расходы</span><strong className="stat__value">32 450 ₽</strong><span className="stat__caption">43% бюджета</span></article>
      <article className="card"><span className="card__eyebrow">К переводу</span><strong className="stat__value">2 400 ₽</strong><span className="stat__caption">2 взаиморасчёта</span></article>
    </div>
  )
}

export default DashboardSummary