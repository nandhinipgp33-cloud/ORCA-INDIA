import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { getApiHealth } from './services/api'
import App from './App'

vi.mock('./services/api', () => ({
  getApiHealth: vi.fn(),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('ORCA INDIA foundation screen', () => {
  it('shows Loading while the health check is pending', () => {
    getApiHealth.mockReturnValue(new Promise(() => {}))

    render(<App />)

    expect(screen.getByText('Loading')).toBeInTheDocument()
  })

  it('shows Connected only after receiving the expected health response', async () => {
    getApiHealth.mockResolvedValue({
      status: 'ok',
      service: 'orca-india-api',
    })

    render(<App />)

    expect(await screen.findByText('Connected')).toBeInTheDocument()
    expect(screen.getByText('No observation data yet')).toBeInTheDocument()
  })

  it('shows Disconnected when the health check fails', async () => {
    getApiHealth.mockRejectedValue(new Error('API is offline'))

    render(<App />)

    expect(await screen.findByText('Disconnected')).toBeInTheDocument()
  })

  it('shows Disconnected for an unexpected health response', async () => {
    getApiHealth.mockResolvedValue({ status: 'ok' })

    render(<App />)

    expect(await screen.findByText('Disconnected')).toBeInTheDocument()
  })
})
