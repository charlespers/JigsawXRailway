import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { BOOK_DEMO, BADGES } from '@/lib/constants'
import { Heading } from '@/components/ui'
import demoVideo from '@/assets/demo.mp4'

export default function BookDemo() {
  const [showVideo, setShowVideo] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  const handlePlayVideo = () => {
    setShowVideo(true)
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.play()
        videoRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  return (
    <div id="demo" className={`flex items-center pt-20 ${showVideo ? 'pb-32' : 'pb-12'} overflow-hidden relative`}>
      {/* Background grid */}
      <div className="absolute inset-0 grid-background opacity-20" />
      
      {/* Subtle circuit trace accent */}
      <div className="absolute top-1/3 left-1/4 w-1/2 h-px bg-gradient-to-r from-transparent via-neon-teal/20 to-transparent" />
      <div className="absolute bottom-1/3 right-1/4 w-1/2 h-px bg-gradient-to-r from-transparent via-electric-orange/20 to-transparent" />

      <div className={`max-w-7xl mx-auto px-6 relative z-10 ${showVideo ? 'py-32' : 'py-12'}`}>
        {/* Accomplishments - Top */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <div className="flex flex-wrap items-center justify-center gap-8 text-sm">
            {BADGES.map((badge, idx) => {
              const content = (
                <motion.span
                  key={idx}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.1 }}
                  className="text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {badge.text}
                </motion.span>
              )
              
              if ('href' in badge && badge.href) {
                return (
                  <a
                    key={idx}
                    href={badge.href}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {content}
                  </a>
                )
              }
              
              return content
            })}
          </div>
        </motion.div>

        {/* Main Headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center mb-12"
        >
          <Heading as="h1" size="2xl" className="mb-6 max-w-6xl mx-auto leading-tight">
            {BOOK_DEMO.headline}
          </Heading>
          <p className="text-xl text-gray-400 leading-relaxed max-w-3xl mx-auto">
            {BOOK_DEMO.subheadline}
          </p>
        </motion.div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="max-w-5xl mx-auto"
        >
          <div className="text-center space-y-4">
            <button
              onClick={handlePlayVideo}
              className="text-base text-neutral-blue hover:text-neon-teal transition-colors inline-flex items-center gap-2 group"
            >
              <span>{BOOK_DEMO.demoLink}</span>
              <span className="group-hover:translate-x-1 transition-transform">→</span>
            </button>
            <div>
              <a
                href="https://tally.so/r/A77Lkz"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-base text-gray-400 hover:text-white transition-colors group"
              >
                <span>{BOOK_DEMO.waitlistLink}</span>
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </a>
            </div>
          </div>
        </motion.div>

        {/* Video Player - Hidden until button is clicked */}
        {showVideo && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-5xl mx-auto mt-8"
          >
            <div className="relative rounded-lg overflow-hidden border border-dark-border bg-black">
              <video
                ref={videoRef}
                src={demoVideo}
                controls
                className="w-full h-auto"
              >
                Your browser does not support the video tag.
              </video>
            </div>
          </motion.div>
        )}

      </div>
    </div>
  )
}
