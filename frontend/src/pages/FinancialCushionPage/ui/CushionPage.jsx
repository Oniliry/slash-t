import StatementAnalysis from "../sections/StatementAnalysis.jsx";
import CushionSummary from "../sections/CushionSummary.jsx";
import CushionHistory from "../sections/CushionHistory.jsx";
import "./CushionPage.css";

function CushionPage() {
  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Финансовая подушка</p>
          <h1>ФинПодушка</h1>
          <p className="page__lead">
            Управление резервным фондом и сбережениями семьи.
          </p>
        </div>
      </header>
      <StatementAnalysis />
      <CushionSummary />
      <CushionHistory />
    </section>
  );
}

export default CushionPage;
