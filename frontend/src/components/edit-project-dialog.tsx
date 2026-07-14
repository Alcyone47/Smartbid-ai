import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"
import { useUpdateProject } from "@/hooks/use-projects"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Project, ProjectStatus } from "@/types/api"

const schema = z.object({
  name: z.string().min(1, "Project name is required"),
  clientName: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

const AUTO = "auto"
const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: AUTO, label: "Auto (from progress)" },
  { value: "draft", label: "Draft" },
  { value: "in_progress", label: "In Progress" },
  { value: "in_review", label: "In Review" },
  { value: "completed", label: "Completed" },
]

export function EditProjectDialog({
  project,
  open,
  onOpenChange,
}: {
  project: Project
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const updateProject = useUpdateProject(project.id)
  const [status, setStatus] = useState<string>(project.status_override ?? AUTO)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: project.name, clientName: project.client_name ?? "" },
  })

  // Re-sync the form whenever the dialog opens for a (possibly different) project.
  useEffect(() => {
    if (open) {
      reset({ name: project.name, clientName: project.client_name ?? "" })
      setStatus(project.status_override ?? AUTO)
    }
  }, [open, project, reset])

  const onSubmit = async (values: FormValues) => {
    try {
      await updateProject.mutateAsync({
        name: values.name,
        client_name: values.clientName || null,
        status_override: status === AUTO ? null : (status as ProjectStatus),
      })
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update project")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit project</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div>
            <Label htmlFor="edit-name" className="mb-1.5">
              Project name
            </Label>
            <Input id="edit-name" placeholder="Enterprise SD-WAN Modernization" {...register("name")} />
            {errors.name ? <p className="mt-1 text-xs text-destructive">{errors.name.message}</p> : null}
          </div>
          <div>
            <Label htmlFor="edit-clientName" className="mb-1.5">
              Client name
            </Label>
            <Input id="edit-clientName" placeholder="Meridian Health" {...register("clientName")} />
          </div>
          <div>
            <Label className="mb-1.5">Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="mt-1 text-xs text-muted-foreground">
              “Auto” follows upload/extraction/matching progress. Any other value pins the status manually.
            </p>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateProject.isPending}>
              {updateProject.isPending ? "Saving…" : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
