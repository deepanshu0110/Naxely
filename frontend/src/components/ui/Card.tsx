import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  padding?: string
  className?: string
}

export default function Card({ children, padding = 'p-4', className }: CardProps) {
  return (
    <div className={`rounded-xl bg-white shadow-md ${padding} ${className ?? ''}`}>
      {children}
    </div>
  )
}
