import BackendStatus from './components/BackendStatus'
import './App.css'

function App() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ORCA India home">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>
            <strong>ORCA INDIA</strong>
            <small>Ocean Resource &amp; Coastal Analytics</small>
          </span>
        </a>
        <BackendStatus />
      </header>

      <section className="welcome">
        <p className="eyebrow">MARINE ECOSYSTEM INTELLIGENCE</p>
        <h1>India&apos;s coast, <span>in context.</span></h1>
        <p className="intro">
          A unified workspace for exploring marine observations, official
          advisories and coastal conditions. Data layers will appear here as
          verified providers are connected.
        </p>
        <div className="foundation-card">
          <div className="card-icon" aria-hidden="true">↗</div>
          <div>
            <h2>Foundation is ready</h2>
            <p>
              Frontend and API are wired together. Ocean measurements are not
              shown until a verified data source is configured.
            </p>
          </div>
          <span className="pill">No observation data yet</span>
        </div>
      </section>

      <footer>
        <span>Built to complement official marine information services.</span>
        <span>Initial validation region: Tamil Nadu</span>
      </footer>
    </main>
  )
}

export default App
