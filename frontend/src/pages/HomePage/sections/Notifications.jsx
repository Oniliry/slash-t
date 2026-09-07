import { useEffect, useState } from 'react'

import './Notifications.css'

const notifications = [
  'Не забудьте проверить расходы за сегодня.',
  'Общий бюджет семьи обновлён.',
  'Проверьте новые взаиморасчёты с участниками семьи.',
  'Финансовая подушка помогает спокойнее планировать месяц.',
]

function Notifications() {
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % notifications.length)
    }, 5000)

    return () => window.clearInterval(intervalId)
  }, [])

  return (
    <article className="notifications" aria-label="Уведомления">
      <div className="notifications__marker" aria-hidden="true">!</div>
      <div className="notifications__content">
        <span className="notifications__title">Уведомления</span>
        <p key={activeIndex} className="notifications__message" aria-live="polite">
          {notifications[activeIndex]}
        </p>
      </div>
      <span className="notifications__counter" aria-hidden="true">
        {activeIndex + 1}/{notifications.length}
      </span>
    </article>
  )
}

export default Notifications
