import {
  BookDemo,
  QuotesBanner,
  CompaniesWhoCare,
  PCBCopilot,
  SimulationSandbox,
  PricingMarket,
} from '@/components/sections'

function App() {
  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Top Right Book Demo Link */}
      <div className="fixed top-6 right-6 z-50">
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

export default App
