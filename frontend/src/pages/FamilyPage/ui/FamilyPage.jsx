import FamilyOverview from "../sections/FamilyOverview.jsx";
import MemberList from "../sections/MemberList.jsx";
import "./FamilyPage.css";

function FamilyPage() {
  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Семейное пространство</p>
          <h1>Семья</h1>
          <p className="page__lead">
            Роли, доходы и честное распределение общих покупок.
          </p>
        </div>
      </header>
      <FamilyOverview />
      <MemberList />
    </section>
  );
}

export default FamilyPage;
