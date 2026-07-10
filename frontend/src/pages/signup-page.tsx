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

const signupSchema = z.object({
  firstName: z.string().min(1, "Required"),
  lastName: z.string().min(1, "Required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "At least 8 characters"),
})

type SignupForm = z.infer<typeof signupSchema>

export function SignupPage() {
  const { signUpWithPassword } = useAuth()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupForm>({ resolver: zodResolver(signupSchema) })

  const onSubmit = async (values: SignupForm) => {
    setIsSubmitting(true)
    const { error } = await signUpWithPassword(values.email, values.password, values.firstName, values.lastName)
    setIsSubmitting(false)
    if (error) {
      toast.error(error)
      return
    }
    toast.success("Check your email to confirm your account.")
    navigate({ to: "/login" })
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

          <h1 className="mb-1.5 text-[26px] font-bold tracking-tight text-foreground">Create your account</h1>
          <p className="mb-7 text-sm text-muted-foreground">Start evaluating vendors in minutes.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Label htmlFor="firstName" className="mb-1.5">
                  First name
                </Label>
                <Input id="firstName" placeholder="Jordan" {...register("firstName")} />
                {errors.firstName ? (
                  <p className="mt-1 text-xs text-destructive">{errors.firstName.message}</p>
                ) : null}
              </div>
              <div className="flex-1">
                <Label htmlFor="lastName" className="mb-1.5">
                  Last name
                </Label>
                <Input id="lastName" placeholder="Reyes" {...register("lastName")} />
                {errors.lastName ? <p className="mt-1 text-xs text-destructive">{errors.lastName.message}</p> : null}
              </div>
            </div>
            <div>
              <Label htmlFor="email" className="mb-1.5">
                Work email
              </Label>
              <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
              {errors.email ? <p className="mt-1 text-xs text-destructive">{errors.email.message}</p> : null}
            </div>
            <div>
              <Label htmlFor="password" className="mb-1.5">
                Password
              </Label>
              <Input id="password" type="password" placeholder="••••••••••" {...register("password")} />
              {errors.password ? <p className="mt-1 text-xs text-destructive">{errors.password.message}</p> : null}
            </div>
            <Button type="submit" disabled={isSubmitting} className="mt-1.5">
              {isSubmitting ? "Creating account…" : "Create account"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-primary">
              Sign in
            </Link>
          </p>
        </div>
      </div>
      <AuthMarketingPanel />
    </div>
  )
}
