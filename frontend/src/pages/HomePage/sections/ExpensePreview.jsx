import "./ExpensePreview.css";

function ExpensePreview() {
  return (
    <article className="card">
      <div className="section-heading">
        <h2>Последние расходы</h2>
        <span className="section-heading__hint">Сентябрь</span>
      </div>
      <div className="list">
        <div className="list__row">
          <span>
            <b>Продукты</b>
            <small>Сегодня · QR-чек</small>
          </span>
          <strong>4 280 ₽</strong>
        </div>
        <div className="list__row">
          <span>
            <b>Коммунальные услуги</b>
            <small>Вчера · общий расход</small>
          </span>
          <strong>6 900 ₽</strong>
        </div>
      </div>
    </article>
  );
}

export default ExpensePreview;
