import './MemberList.css'

function MemberList() {
  return <article className="card"><div className="section-heading"><h2>Участники семьи</h2><span className="section-heading__hint">3 участника</span></div><div className="list"><div className="list__row"><span><b>Алексей Белов</b><small>Взрослый · владелец семьи · 60%</small></span><strong>90 000 ₽</strong></div><div className="list__row"><span><b>Мария Петрова</b><small>Взрослый · 40%</small></span><strong>60 000 ₽</strong></div><div className="list__row"><span><b>Илья Петров</b><small>Ребёнок · получает переводы</small></span><strong>—</strong></div></div></article>
}

export default MemberList