import { BrowserRouter, Routes, Route } from 'react-router-dom'
import {
  BookDemo,
  QuotesBanner,
  CompaniesWhoCare,
  PCBCopilot,
  SimulationSandbox,
  PricingMarket,
} from '@/components/sections'
import { DemoAuth, DemoPage } from '@/pages'
import Button from '@/components/ui/Button'

function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Top Right Buttons */}
      <div className="fixed top-6 right-6 z-50 flex items-center gap-4">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => window.location.href = '/demo/auth'}
          className="text-base"
        >
          Start your demo
        </Button>
        <a
          href="https://calendar.app.google/vKCFkPPsfraoG79z9"
          target="_blank"
          rel="noopener noreferrer"
          className="text-base text-neutral-blue hover:text-neon-teal transition-colors inline-flex items-center gap-2 group"
        >
          <span>Book a demo</span>
          <span className="group-hover:translate-x-1 transition-transform">→</span>
        </a>
      </div>

      <BookDemo />
      <QuotesBanner />
      <CompaniesWhoCare />
      <PCBCopilot />
      <SimulationSandbox />
      <PricingMarket />
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/demo/auth" element={<DemoAuth />} />
        <Route path="/demo" element={<DemoPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
