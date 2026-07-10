import { useRef, useState } from "react"
import { toast } from "sonner"
import { Upload } from "lucide-react"
import { useUploadDocument } from "@/hooks/use-documents"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import type { DocType } from "@/types/api"

export function DocumentUploadDialog({
  projectId,
  docType,
  triggerLabel,
}: {
  projectId: string
  docType: DocType
  triggerLabel: string
}) {
  const [open, setOpen] = useState(false)
  const [vendorName, setVendorName] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadDocument = useUploadDocument(projectId)

  const handleSubmit = async () => {
    const file = fileInputRef.current?.files?.[0]
    if (!file) {
      toast.error("Choose a file to upload")
      return
    }
    if (docType === "vendor_proposal" && !vendorName.trim()) {
      toast.error("Vendor name is required")
      return
    }
    try {
      await uploadDocument.mutateAsync({ file, docType, vendorName: vendorName || undefined })
      setOpen(false)
      setVendorName("")
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Upload failed")
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <button onClick={() => setOpen(true)} className="text-xs font-semibold text-primary">
        + {triggerLabel}
      </button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{triggerLabel}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          {docType === "vendor_proposal" ? (
            <div>
              <Label htmlFor="vendorName" className="mb-1.5">
                Vendor name
              </Label>
              <Input
                id="vendorName"
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
                placeholder="Nexbridge Networks"
              />
            </div>
          ) : null}
          <div>
            <Label htmlFor="file" className="mb-1.5">
              File
            </Label>
            <Input id="file" type="file" ref={fileInputRef} accept=".pdf,.docx" />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSubmit} disabled={uploadDocument.isPending}>
            <Upload size={14} />
            {uploadDocument.isPending ? "Uploading…" : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
