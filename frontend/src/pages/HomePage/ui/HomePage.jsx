import DashboardSummary from "../sections/DashboardSummary.jsx";
import CushionWidget from "../sections/CushionWidget.jsx";
import DebtsWidget from "../sections/DebtsWidget.jsx";
import ExpensePreview from "../sections/ExpensePreview.jsx";
import "./HomePage.css";

function HomePage() {
  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Семейный бюджет</p>
          <h1>Главная</h1>
          <p className="page__lead">
            Общий обзор бюджета, трат и взаиморасчётов семьи.
          </p>
        </div>
      </header>
      <DashboardSummary />
      <DebtsWidget />
      <CushionWidget />
      <ExpensePreview />
    </section>
  );
}

export default HomePage;
