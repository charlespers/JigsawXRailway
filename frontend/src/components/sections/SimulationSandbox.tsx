import { motion } from 'framer-motion'
import { SIMULATION_SANDBOX } from '@/lib/constants'
import { Heading } from '@/components/ui'
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver'
import droneSwarm from '@/assets/droneswarm.png'

export default function SimulationSandbox() {
  const { ref, hasIntersected } = useIntersectionObserver()

  return (
    <div id="simulation" ref={ref} className="py-20 relative px-6">
      <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
        className="text-center mb-16"
      >
        <Heading size="lg" className="mb-4 max-w-5xl mx-auto">{SIMULATION_SANDBOX.title}</Heading>
        <p className="text-lg text-gray-400 max-w-5xl mx-auto mb-2">
          {SIMULATION_SANDBOX.subtitle}
        </p>
        <p className="text-base text-gray-500 max-w-5xl mx-auto">
          {SIMULATION_SANDBOX.description}
        </p>
      </motion.div>

      {/* Main Image */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={hasIntersected ? { opacity: 1, scale: 1 } : {}}
        transition={{ delay: 0.2 }}
        className="mb-20"
      >
        <div className="max-w-5xl mx-auto">
          <img
            src={droneSwarm}
            alt="Robotics simulation sandbox"
            className="w-full h-auto rounded-lg"
          />
        </div>
      </motion.div>

      {/* Steps - Horizontal Chart with Lines */}
      <div className="max-w-5xl mx-auto">
        <div className="border-[4px] border-gray-400 rounded-lg overflow-hidden">
          {/* Header Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 border-b-[4px] border-gray-400">
            {SIMULATION_SANDBOX.steps.map((step, idx) => (
              <motion.div
                key={`header-${idx}`}
                initial={{ opacity: 0, y: 20 }}
                animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.3 + idx * 0.1 }}
                className={`p-6 ${idx < SIMULATION_SANDBOX.steps.length - 1 ? 'border-r-[4px] border-gray-400' : ''}`}
              >
                <h3 className="text-lg font-semibold text-white">{step.title}</h3>
              </motion.div>
            ))}
          </div>
          {/* Description Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {SIMULATION_SANDBOX.steps.map((step, idx) => (
              <motion.div
                key={`desc-${idx}`}
                initial={{ opacity: 0, y: 20 }}
                animate={hasIntersected ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.4 + idx * 0.1 }}
                className={`p-6 ${idx < SIMULATION_SANDBOX.steps.length - 1 ? 'border-r-[4px] border-gray-400' : ''}`}
              >
                <ul className="space-y-2">
                  {step.description.map((bullet, bulletIdx) => (
                    <li key={bulletIdx} className="text-sm text-gray-400 flex items-start">
                      <span className="text-gray-300 mr-2">•</span>
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}
