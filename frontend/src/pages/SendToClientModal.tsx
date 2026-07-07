import { useState } from 'react'
import { Send, X } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import api from '@/lib/axios'

interface SendToClientModalProps {
  isOpen: boolean
  onClose: () => void
  reportId: string
  reportTitle: string
}

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function SendToClientModal({ isOpen, onClose, reportId, reportTitle }: SendToClientModalProps) {
  const [emailInput, setEmailInput] = useState('')
  const [emails, setEmails] = useState<string[]>([])
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addEmail()
    }
  }

  function addEmail() {
    const val = emailInput.trim().replace(/,+$/, '')
    if (!val) return
    if (!emailRegex.test(val)) {
      setError('Invalid email format')
      return
    }
    setError(null)
    if (!emails.includes(val)) {
      setEmails([...emails, val])
    }
    setEmailInput('')
  }

  function removeEmail(email: string) {
    setEmails(emails.filter((e) => e !== email))
  }

  function handlePaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData('text')
    if (text.includes(',') || text.includes('\n') || text.includes(';')) {
      e.preventDefault()
      const parts = text.split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean)
      const added: string[] = []
      for (const part of parts) {
        if (emailRegex.test(part) && !emails.includes(part) && !added.includes(part)) {
          added.push(part)
        }
      }
      setEmails([...emails, ...added])
    }
  }

  async function handleSend() {
    if (emails.length === 0) {
      setError('At least one recipient is required')
      return
    }
    setError(null)
    setSending(true)
    try {
      await api.post(`/reports/${reportId}/send`, {
        recipients: emails,
        message: message.trim() || undefined,
      })
      toast.success('Report sent to client!')
      setEmails([])
      setMessage('')
      setEmailInput('')
      onClose()
    } catch {
      // axios interceptor shows the backend error via toast.error
    } finally {
      setSending(false)
    }
  }

  function handleClose() {
    setEmails([])
    setMessage('')
    setEmailInput('')
    setError(null)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Send Report to Client">
      <p className="mb-3 text-sm text-gray-500 dark:text-gray-400">
        Send <strong>{reportTitle}</strong> to your client via email.
      </p>
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-ink dark:text-gray-300">
            Recipients
          </label>
          <div className="flex flex-wrap gap-1.5 rounded-lg border border-gray-300 bg-white p-2 dark:border-gray-600 dark:bg-darkBg">
            {emails.map((email) => (
              <span
                key={email}
                className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
              >
                {email}
                <button
                  onClick={() => removeEmail(email)}
                  className="ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full hover:bg-amber-200 dark:hover:bg-amber-800"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            <input
              type="text"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              onBlur={addEmail}
              placeholder={emails.length === 0 ? 'Enter email, press Enter or comma' : 'Add more...'}
              className="min-w-[160px] flex-1 border-0 bg-transparent text-sm text-ink outline-none placeholder:text-gray-400 dark:text-gray-100"
            />
          </div>
          {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
          <p className="mt-1 text-xs text-gray-400">Press Enter or comma to add each recipient</p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink dark:text-gray-300">
            Message <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add a personal note..."
            rows={3}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-ink outline-none placeholder:text-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 dark:border-gray-600 dark:bg-darkBg dark:text-gray-100"
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" size="md" onClick={handleClose}>
            Cancel
          </Button>
          <Button variant="primary" size="md" loading={sending} onClick={handleSend}>
            <Send className="mr-1.5 h-4 w-4" /> Send
          </Button>
        </div>
      </div>
    </Modal>
  )
}
