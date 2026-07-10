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
