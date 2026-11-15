import { useEffect, useState } from 'react'
import { getApiHealth } from '../services/api'

function BackendStatus() {
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let active = true

    getApiHealth()
      .then((health) => {
        if (active) {
          setStatus(
            health?.status === 'ok' && health?.service === 'orca-india-api'
              ? 'connected'
              : 'disconnected',
          )
        }
      })
      .catch(() => {
        if (active) setStatus('disconnected')
      })

    return () => {
      active = false
    }
  }, [])

  const label = {
    loading: 'Loading',
    connected: 'Connected',
    disconnected: 'Disconnected',
  }[status]

  return (
    <div className={`api-status api-status--${status}`} role="status">
      <span className="status-dot" />
      {label}
    </div>
  )
}

export default BackendStatus
