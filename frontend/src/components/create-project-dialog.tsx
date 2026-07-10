import { useState } from "react"
import { useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Plus } from "lucide-react"
import { useCreateProject } from "@/hooks/use-projects"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog"

const schema = z.object({
  name: z.string().min(1, "Project name is required"),
  clientName: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function CreateProjectDialog() {
  const [open, setOpen] = useState(false)
  const createProject = useCreateProject()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      const project = await createProject.mutateAsync({ name: values.name, client_name: values.clientName || null })
      setOpen(false)
      reset()
      navigate({ to: "/projects/$projectId", params: { projectId: project.id } })
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create project")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus size={15} strokeWidth={2.5} />
          New Project
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New project</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div>
            <Label htmlFor="name" className="mb-1.5">
              Project name
            </Label>
            <Input id="name" placeholder="Enterprise SD-WAN Modernization" {...register("name")} />
            {errors.name ? <p className="mt-1 text-xs text-destructive">{errors.name.message}</p> : null}
          </div>
          <div>
            <Label htmlFor="clientName" className="mb-1.5">
              Client name
            </Label>
            <Input id="clientName" placeholder="Meridian Health" {...register("clientName")} />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? "Creating…" : "Create project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
