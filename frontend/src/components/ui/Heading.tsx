import { HTMLAttributes, forwardRef, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
  gradient?: boolean
  children: ReactNode
}

const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ as: Component = 'h2', size = 'lg', gradient = false, className, children, ...props }, ref) => {
    const sizes = {
      xs: 'text-xl',
      sm: 'text-2xl',
      md: 'text-3xl',
      lg: 'text-3xl lg:text-4xl', // Reduced from 4xl/5xl
      xl: 'text-4xl lg:text-5xl', // Reduced from 5xl/6xl
      '2xl': 'text-5xl lg:text-6xl', // Hero size
      '3xl': 'text-6xl lg:text-7xl',
    }
    
    const gradientStyles = gradient
      ? 'bg-gradient-to-r from-white via-gray-300 to-gray-500 bg-clip-text text-transparent'
      : ''
    
    return (
      <Component
        ref={ref}
        className={cn(
          'font-bold leading-tight tracking-tight',
          sizes[size],
          gradientStyles,
          className
        )}
        {...props}
      >
        {children}
      </Component>
    )
  }
)

Heading.displayName = 'Heading'

export default Heading

