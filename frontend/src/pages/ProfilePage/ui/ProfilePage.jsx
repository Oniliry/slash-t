import ProfileDetails from "../sections/ProfileDetails.jsx";
import ReminderSettings from "../sections/ReminderSettings.jsx";
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
      <ProfileDetails />
      <ReminderSettings />
    </section>
  );
}

export default ProfilePage;
