import "./ReminderSettings.css";

function ReminderSettings() {
  return (
    <article className="card">
      <p className="card__eyebrow">Настройки</p>
      <h2>Напоминания о переводах</h2>
      <p className="card__muted">
        Мягкое напоминание должникам раз в 7 дней. Погашение подтверждает
        получатель.
      </p>
    </article>
  );
}

export default ReminderSettings;
