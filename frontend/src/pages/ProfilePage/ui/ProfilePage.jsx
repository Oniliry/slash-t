import NameWidget from "../sections/NameWidget.jsx";
import RoleWidget from "../sections/RoleWidget.jsx";
import PasswordWidget from "../sections/PasswordWidget.jsx";
import "./ProfilePage.css";

function ProfilePage() {
  return (
    <section className="page">
      <header className="page__header">
        <div>
          <p className="page__eyebrow">Личный кабинет</p>
          <h1>Профиль</h1>
          <p className="page__lead">Ваши данные и роль в семейном бюджете.</p>
        </div>
      </header>
      <NameWidget />
      <RoleWidget />
      <PasswordWidget />
    </section>
  );
}

export default ProfilePage;
