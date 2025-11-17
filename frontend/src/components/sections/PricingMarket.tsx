import { motion } from 'framer-motion'
import { INDUSTRIES, REACH_OUT, MARKET_OVERVIEW } from '@/lib/constants'
import { Heading } from '@/components/ui'
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver'

export default function PricingMarket() {
  const { ref, hasIntersected } = useIntersectionObserver()

  return (
    <div id="pricing" ref={ref} className="py-20 relative px-6">
      <div className="max-w-7xl mx-auto">
      <div className="max-w-5xl mx-auto space-y-20">
        {/* Market Opportunity Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
          className="space-y-8"
        >
          <div className="text-center mb-12">
            <Heading size="lg" className="mb-4 max-w-5xl mx-auto">Market Opportunity</Heading>
            <p className="text-base text-gray-500 max-w-5xl mx-auto">
              {MARKET_OVERVIEW.totalMarket}. {MARKET_OVERVIEW.growth}. {MARKET_OVERVIEW.opportunity}
            </p>
          </div>

          {/* Market Chart */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-8 border border-gray-600 rounded-lg">
              <div className="text-xs font-mono uppercase tracking-wide text-gray-500 mb-3">
                TAM – PCB design software
              </div>
              <p className="text-4xl font-semibold text-white mb-2">$3.8B</p>
              <p className="text-sm text-gray-400">Global market in 2023</p>
            </div>
            <div className="p-8 border border-gray-600 rounded-lg">
              <div className="text-xs font-mono uppercase tracking-wide text-gray-500 mb-3">
                Growing fast
              </div>
              <p className="text-4xl font-semibold text-white mb-2">$11–12B</p>
              <p className="text-sm text-gray-400">Projected by 2032 (12–14% CAGR)</p>
            </div>
            <div className="p-8 border border-gray-600 rounded-lg">
              <div className="text-xs font-mono uppercase tracking-wide text-gray-500 mb-3">
                Initial wedge
              </div>
              <p className="text-4xl font-semibold text-white mb-2">$10M+</p>
              <p className="text-sm text-gray-400">ARR at just 1% of the market</p>
            </div>
          </div>
        </motion.div>

        {/* Industries Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.1 }}
          className="space-y-8"
        >
          <Heading size="md" className="text-center max-w-5xl mx-auto">
            Where we start
          </Heading>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {INDUSTRIES.map((industry, _idx) => (
              <div
                key={industry.name}
                className="p-6 border border-gray-600 rounded-lg"
              >
                <h3 className="text-lg font-semibold text-white mb-3">{industry.name}</h3>
                <p className="text-sm text-gray-400 leading-relaxed mb-3">
                  {industry.pain}
                </p>
                <p className="text-xs text-gray-500 font-mono">
                  {industry.market}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Reach Out */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2 }}
          className="max-w-4xl mx-auto"
        >
          <div className="text-center mb-12">
            <Heading size="lg" className="mb-8">{REACH_OUT.headline}</Heading>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start max-w-2xl mx-auto">
            {/* Book Demo */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.3 }}
              className="text-center space-y-4"
            >
              <div className="text-xs font-mono uppercase tracking-wider text-gray-500 mb-4">
                Demo
              </div>
              <a
                href={REACH_OUT.bookingLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-lg font-medium text-white hover:text-gray-300 transition-all group"
              >
                <span>Book a demo</span>
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </a>
            </motion.div>
            
            {/* Email */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.4 }}
              className="text-center space-y-4"
            >
              <div className="text-xs font-mono uppercase tracking-wider text-gray-500 mb-4">
                Email
              </div>
              <a
                href={`mailto:${REACH_OUT.email}`}
                className="text-lg font-medium text-white hover:text-gray-300 transition-colors block"
              >
                {REACH_OUT.email}
              </a>
            </motion.div>
          </div>
        </motion.div>
      </div>
      </div>
    </div>
  )
}
