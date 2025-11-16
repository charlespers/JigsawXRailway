import { INDUSTRY_QUOTES } from '@/lib/constants'

export default function QuotesBanner() {
  // Duplicate quotes for seamless loop
  const duplicatedQuotes = [...INDUSTRY_QUOTES, ...INDUSTRY_QUOTES]

  return (
    <div className="py-6 overflow-hidden relative w-full">
      {/* Gradient overlays for fade effect */}
      <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-dark-bg to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-dark-bg to-transparent z-10 pointer-events-none" />
      
      <div className="flex animate-scroll items-center">
        {duplicatedQuotes.map((quote, idx) => (
          <div
            key={`${quote.author}-${idx}`}
            className="flex-shrink-0 mx-6 w-80"
          >
            <div className="text-sm text-gray-400 italic mb-1 line-clamp-2">
              "{quote.quote}"
            </div>
            <div className="text-xs text-gray-500">
              — {quote.author}, {quote.title}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

