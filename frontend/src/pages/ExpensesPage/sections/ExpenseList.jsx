import './ExpenseList.css'

function ExpenseList() {
  return <article className="card"><div className="section-heading"><h2>История покупок</h2><span className="section-heading__hint">Все категории</span></div><div className="list"><div className="list__row"><span><b>Продукты · Перекрёсток</b><small>Сегодня · Алексей · общий расход</small></span><strong>4 280 ₽</strong></div><div className="list__row"><span><b>Коммунальные услуги</b><small>Вчера · автоматический платёж</small></span><strong>6 900 ₽</strong></div><div className="list__row"><span><b>Кофе и перекус</b><small>4 сент. · личный расход</small></span><strong>380 ₽</strong></div></div></article>
}

export default ExpenseList