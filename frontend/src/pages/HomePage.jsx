import { useEffect, useState } from 'react'

function HomePage() {
  const [serviceText, setServiceText] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let isCurrent = true

    fetch('http://localhost:8000/slash-t')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.text()
      })
      .then((text) => {
        if (isCurrent) {
          setServiceText(text)
        }
      })
      .catch(() => {
        if (isCurrent) {
          setError('Не удалось подключиться к backend')
        }
      })

    return () => {
      isCurrent = false
    }
  }, [])

  return (
    <section>
      <h1>Главная (pc1)</h1>
      {error ? <p>{error}</p> : <p>{serviceText || 'Загрузка...'}</p>}
    </section>
  )
}

export default HomePage