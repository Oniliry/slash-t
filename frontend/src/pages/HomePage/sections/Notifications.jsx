import { useEffect, useState } from 'react'

import { getAiNotification, getNotifications } from '../../../shared/api/notifications.ts'

import './Notifications.css'

function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    let isMounted = true

    async function loadNotifications() {
      const response = await getNotifications()
      if (!isMounted) return

      if (!response.error && response.data?.length) {
        setNotifications(response.data)
        setActiveIndex(0)

        getAiNotification().then((adviceResponse) => {
          if (!isMounted || adviceResponse.error || !adviceResponse.data) return

          setNotifications((currentNotifications) => [
            adviceResponse.data,
            ...currentNotifications.filter((item) => item.kind !== 'advice'),
          ].slice(0, 6))
        })
      } else {
        setNotifications([
          {
            kind: 'family',
            text: response.message ?? 'Нет новых уведомлений.',
          },
        ])
      }
    }

    loadNotifications()

    const refreshId = window.setInterval(() => {
      loadNotifications()
    }, 60000)

    return () => {
      isMounted = false
      window.clearInterval(refreshId)
    }
  }, [])

  useEffect(() => {
    if (notifications.length < 2) return undefined

    const intervalId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % notifications.length)
    }, 15000)

    return () => window.clearInterval(intervalId)
  }, [notifications.length])

  const current = notifications[activeIndex]
  const showPrevious = () => {
    setActiveIndex((currentIndex) => (currentIndex - 1 + notifications.length) % notifications.length)
  }
  const showNext = () => {
    setActiveIndex((currentIndex) => (currentIndex + 1) % notifications.length)
  }

  return (
    <article className="notifications" aria-label="Уведомления">
      <div className="notifications__marker" aria-hidden="true">!</div>
      <div className="notifications__content">
        <span className="notifications__title">Уведомления</span>
        <p key={current?.text ?? 'placeholder'} className="notifications__message" aria-live="polite">
          {current?.text ?? 'Загрузка уведомлений...'}
        </p>
      </div>
      {notifications.length > 1 && (
        <div className="notifications__controls">
          <button
            className="notifications__button"
            type="button"
            title="Предыдущее уведомление"
            aria-label="Предыдущее уведомление"
            onClick={showPrevious}
          >
            ‹
          </button>
          <span className="notifications__counter" aria-live="polite">
            {activeIndex + 1}/{notifications.length}
          </span>
          <button
            className="notifications__button"
            type="button"
            title="Следующее уведомление"
            aria-label="Следующее уведомление"
            onClick={showNext}
          >
            ›
          </button>
        </div>
      )}
    </article>
  )
}

export default Notifications
