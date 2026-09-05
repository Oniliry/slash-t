import './ExpenseSummary.css'

function ExpenseSummary() {
  return <div className="stats-grid"><article className="card"><span className="card__eyebrow">Всего за месяц</span><strong className="stat__value">48 320 ₽</strong><span className="stat__caption">из 75 000 ₽</span></article><article className="card"><span className="card__eyebrow">Общие</span><strong className="stat__value">32 450 ₽</strong><span className="stat__caption">67% всех трат</span></article><article className="card"><span className="card__eyebrow">Личные</span><strong className="stat__value">15 870 ₽</strong><span className="stat__caption">33% всех трат</span></article></div>
}

export default ExpenseSummary