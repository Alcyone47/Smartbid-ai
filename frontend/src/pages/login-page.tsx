import { useState } from "react"
import { Link, useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AuthMarketingPanel } from "@/components/auth-marketing-panel"

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
})

type LoginForm = z.infer<typeof loginSchema>

export function LoginPage() {
  const { signInWithPassword, signInWithGoogle } = useAuth()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) })

  const onSubmit = async (values: LoginForm) => {
    setIsSubmitting(true)
    const { error } = await signInWithPassword(values.email, values.password)
    setIsSubmitting(false)
    if (error) {
      toast.error(error)
      return
    }
    navigate({ to: "/" })
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="flex flex-1 items-center justify-center p-12">
        <div className="w-full max-w-[400px]">
          <div className="mb-10 flex items-center gap-2.5">
            <div className="flex h-[34px] w-[34px] items-center justify-center rounded-[9px] bg-primary">
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
                <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" fill="#fff" />
              </svg>
            </div>
            <span className="text-[17px] font-bold tracking-tight text-foreground">SmartBid AI</span>
          </div>

          <h1 className="mb-1.5 text-[26px] font-bold tracking-tight text-foreground">Welcome back</h1>
          <p className="mb-7 text-sm text-muted-foreground">Sign in to continue evaluating vendor proposals.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div>
              <Label htmlFor="email" className="mb-1.5">
                Work email
              </Label>
              <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
              {errors.email ? <p className="mt-1 text-xs text-destructive">{errors.email.message}</p> : null}
            </div>
            <div>
              <div className="mb-1.5 flex justify-between">
                <Label htmlFor="password">Password</Label>
                <a href="#" className="text-[12.5px] font-medium text-primary">
                  Forgot?
                </a>
              </div>
              <Input id="password" type="password" placeholder="••••••••••" {...register("password")} />
              {errors.password ? <p className="mt-1 text-xs text-destructive">{errors.password.message}</p> : null}
            </div>
            <Button type="submit" disabled={isSubmitting} className="mt-1.5">
              {isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">OR</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <Button variant="outline" className="w-full" onClick={() => signInWithGoogle()}>
            Continue with Google
          </Button>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            No account?{" "}
            <Link to="/signup" className="font-semibold text-primary">
              Sign up
            </Link>
          </p>
        </div>
      </div>
      <AuthMarketingPanel />
    </div>
  )
}
