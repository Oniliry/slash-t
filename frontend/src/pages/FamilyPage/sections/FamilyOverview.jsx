import './FamilyOverview.css'

function FamilyOverview() {
  return <div className="overview-grid"><article className="card"><p className="card__eyebrow">Беловы</p><h2>Общий бюджет · 75 000 ₽</h2><div className="split"><span style={{ width: '60%' }}>Алексей 60%</span><span style={{ width: '40%' }}>Мария 40%</span></div></article><article className="card"><p className="card__eyebrow">Расчёты</p><h2>2 400 ₽</h2><p className="card__muted">к переводу участникам</p></article></div>
}

export default FamilyOverview