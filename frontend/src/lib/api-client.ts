import { supabase } from "@/lib/supabase"
import type { ApiErrorBody } from "@/types/api"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string

export class ApiError extends Error {
  errorCode: string
  status: number

  constructor(message: string, errorCode: string, status: number) {
    super(message)
    this.errorCode = errorCode
    this.status = status
  }
}

async function getAuthHeader(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

interface RequestOptions {
  method?: string
  body?: unknown
  formData?: FormData
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const authHeader = await getAuthHeader()
  const headers: Record<string, string> = { ...authHeader }

  let body: BodyInit | undefined
  if (options.formData) {
    body = options.formData
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json"
    body = JSON.stringify(options.body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body,
  })

  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json()

  if (!response.ok) {
    const errorBody = data as ApiErrorBody
    throw new ApiError(errorBody.message ?? "Request failed", errorBody.error_code ?? "UNKNOWN", response.status)
  }

  return data as T
}

function filenameFromDisposition(header: string | null): string | undefined {
  if (!header) return undefined
  const match = /filename="?([^"]+)"?/.exec(header)
  return match?.[1]
}

/** Fetch an authenticated binary response and trigger a browser download. */
export async function downloadFile(path: string, fallbackFilename: string): Promise<void> {
  const authHeader = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: authHeader })

  if (!response.ok) {
    let message = "Download failed"
    let errorCode = "UNKNOWN"
    try {
      const errorBody = (await response.json()) as ApiErrorBody
      message = errorBody.message ?? message
      errorCode = errorBody.error_code ?? errorCode
    } catch {
      // non-JSON error body; keep defaults
    }
    throw new ApiError(message, errorCode, response.status)
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filenameFromDisposition(response.headers.get("Content-Disposition")) ?? fallbackFilename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
