import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  padding?: string
  className?: string
}

export default function Card({ children, padding = 'p-4', className }: CardProps) {
  return (
    <div className={`rounded-xl bg-paper text-ink shadow-md ${padding} ${className ?? ''} dark:bg-ink dark:text-paper`}>
      {children}
    </div>
  )
}
