import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { CloudUpload, FileText, X } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { useReportStore } from '@/store/reportStore'
import type { UploadResult } from '@/types/report'
import toast from 'react-hot-toast'

interface FileUploadProps {
  onUploadComplete: (result: UploadResult) => void
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const uploadFile = useReportStore((s) => s.uploadFile)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return
      setUploading(true)
      setError(null)
      try {
        const result = await uploadFile(file)
        setUploadResult(result)
        onUploadComplete(result)
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed. Please try again.'
        setError(msg)
        toast.error(msg)
      } finally {
        setUploading(false)
      }
    },
    [uploadFile, onUploadComplete],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxFiles: 1,
    disabled: uploading || !!uploadResult,
  })

  const reset = () => {
    setUploadResult(null)
    setError(null)
  }

  if (uploadResult) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-green-600" />
            <div>
              <p className="font-medium text-gray-900">{uploadResult.filename}</p>
              <p className="text-sm text-gray-500">
                {uploadResult.row_count.toLocaleString()} rows × {uploadResult.column_count} columns
              </p>
            </div>
          </div>
          <button onClick={reset} className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors ${
          isDragActive
            ? 'border-indigo-400 bg-indigo-50'
            : error
              ? 'border-red-300 bg-red-50'
              : 'border-gray-300 bg-gray-50 hover:border-indigo-300 hover:bg-indigo-50/50'
        }`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Spinner size="lg" />
            <p className="text-sm text-gray-600">Uploading...</p>
          </div>
        ) : (
          <>
            <CloudUpload className="mb-4 h-12 w-12 text-gray-400" />
            <p className="mb-1 text-sm font-medium text-gray-700">
              {isDragActive ? 'Drop your file here' : 'Drag & drop your CSV or XLSX file'}
            </p>
            <p className="text-xs text-gray-500">or click to browse</p>
          </>
        )}
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
