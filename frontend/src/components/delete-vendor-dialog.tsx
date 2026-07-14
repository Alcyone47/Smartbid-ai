import { toast } from "sonner"
import { useDeleteVendor } from "@/hooks/use-vendors"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"

export function DeleteVendorDialog({
  projectId,
  vendorId,
  vendorName,
  open,
  onOpenChange,
}: {
  projectId: string
  vendorId: string
  vendorName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const deleteVendor = useDeleteVendor(projectId)

  const onConfirm = async () => {
    try {
      await deleteVendor.mutateAsync(vendorId)
      onOpenChange(false)
      toast.success("Vendor removed")
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to remove vendor")
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove vendor</DialogTitle>
        </DialogHeader>
        <p className="text-[13.5px] leading-relaxed text-muted-foreground">
          Remove <span className="font-semibold text-foreground">{vendorName}</span>? This permanently
          deletes all of its uploaded PDFs, extracted specifications, and its column in the compliance
          matrix. This action cannot be undone.
        </p>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={deleteVendor.isPending}>
            {deleteVendor.isPending ? "Removing…" : "Remove vendor"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
