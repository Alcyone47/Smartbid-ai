import { toast } from "sonner"
import { useDeleteProject } from "@/hooks/use-projects"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import type { Project } from "@/types/api"

export function DeleteProjectDialog({
  project,
  open,
  onOpenChange,
  onDeleted,
}: {
  project: Project
  open: boolean
  onOpenChange: (open: boolean) => void
  onDeleted?: () => void
}) {
  const deleteProject = useDeleteProject()

  const onConfirm = async () => {
    try {
      await deleteProject.mutateAsync(project.id)
      onOpenChange(false)
      toast.success("Project deleted")
      onDeleted?.()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete project")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete project</DialogTitle>
        </DialogHeader>
        <p className="text-[13.5px] leading-relaxed text-muted-foreground">
          Delete <span className="font-semibold text-foreground">{project.name}</span>? This permanently
          removes the project along with all of its documents, extracted requirements and specifications,
          and compliance results. This action cannot be undone.
        </p>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={deleteProject.isPending}>
            {deleteProject.isPending ? "Deleting…" : "Delete project"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
