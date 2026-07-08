import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
}

export default function Modal({ isOpen, onClose, title, children, footer }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose()
      }}
    >
      <div className="mx-4 flex w-full max-w-md flex-col rounded-xl bg-paper text-ink shadow-lg max-h-[calc(100vh-3rem)] dark:bg-darkBg dark:text-paper">
        <div className="flex-shrink-0 px-6 pt-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-body font-semibold text-ink dark:text-gray-100">{title}</h2>
            <button onClick={onClose} className="rounded-md p-1 text-gray-400 transition-colors duration-150 ease-in-out hover:bg-slate hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:hover:bg-gray-700 dark:hover:text-gray-300">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6">
          {children}
        </div>
        {footer && (
          <div className="flex-shrink-0 border-t border-gray-200 px-6 pb-6 pt-4 dark:border-gray-700">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
