import { useEffect, useState } from "react";

import DashboardSummary from "../sections/DashboardSummary.jsx";
import ExpensePreview from "../sections/ExpensePreview.jsx";
import "./HomePage.css";

function HomePage() {
  const [serviceText, setServiceText] = useState("");

  useEffect(() => {
    let isCurrent = true;

    fetch("http://localhost:8000/slash-t")
      .then((response) => (response.ok ? response.text() : Promise.reject()))
      .then((text) => {
        if (isCurrent) setServiceText(text);
      })
      .catch(() => {});

    return () => {
      isCurrent = false;
    };
  }, []);

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
        <span className="page__status">{serviceText || "Семья Беловых"}</span>
      </header>
      <DashboardSummary />
      <ExpensePreview />
    </section>
  );
}

export default HomePage;
