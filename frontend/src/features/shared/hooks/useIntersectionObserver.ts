import { useEffect, useRef, useState, RefObject } from 'react'

/**
 * Hook to observe element intersection with viewport
 */
export function useIntersectionObserver<T extends HTMLElement = HTMLElement>(
  options?: IntersectionObserverInit
): {
  ref: RefObject<T>
  isIntersecting: boolean
  hasIntersected: boolean
} {
  const [isIntersecting, setIsIntersecting] = useState(false)
  const [hasIntersected, setHasIntersected] = useState(false)
  const ref = useRef<T>(null)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting)
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true)
        }
      },
      {
        threshold: 0.1,
        ...options,
      }
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [options, hasIntersected])

  return { ref, isIntersecting, hasIntersected }
}

