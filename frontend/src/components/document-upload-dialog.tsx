import { useRef, useState } from "react"
import { toast } from "sonner"
import { Upload } from "lucide-react"
import { useUploadDocument } from "@/hooks/use-documents"
import { useVendors } from "@/hooks/use-vendors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import type { DocType } from "@/types/api"

export function DocumentUploadDialog({
  projectId,
  docType,
  triggerLabel,
  presetVendorName,
}: {
  projectId: string
  docType: DocType
  triggerLabel: string
  // When set (adding files to an existing vendor), the vendor field is locked.
  presetVendorName?: string
}) {
  const [open, setOpen] = useState(false)
  const [vendorName, setVendorName] = useState(presetVendorName ?? "")
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadDocument = useUploadDocument(projectId)
  const { data: vendors } = useVendors(projectId)

  const isVendor = docType === "vendor_proposal"
  const lockedVendor = isVendor && !!presetVendorName

  const reset = () => {
    setVendorName(presetVendorName ?? "")
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleSubmit = async () => {
    const files = Array.from(fileInputRef.current?.files ?? [])
    if (files.length === 0) {
      toast.error("Choose at least one file to upload")
      return
    }
    const name = (presetVendorName ?? vendorName).trim()
    if (isVendor && !name) {
      toast.error("Vendor name is required")
      return
    }
    setUploading(true)
    try {
      for (const file of files) {
        await uploadDocument.mutateAsync({ file, docType, vendorName: name || undefined })
      }
      toast.success(files.length > 1 ? `${files.length} files uploaded` : "File uploaded")
      setOpen(false)
      reset()
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Upload failed")
    } finally {
      setUploading(false)
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
          {isVendor ? (
            <div>
              <Label htmlFor="vendorName" className="mb-1.5">
                Vendor name
              </Label>
              <Input
                id="vendorName"
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
                placeholder="Nexbridge Networks"
                list="vendor-name-options"
                disabled={lockedVendor}
              />
              {!lockedVendor ? (
                <datalist id="vendor-name-options">
                  {(vendors ?? []).map((v) => (
                    <option key={v.id} value={v.name} />
                  ))}
                </datalist>
              ) : null}
            </div>
          ) : null}
          <div>
            <Label htmlFor="file" className="mb-1.5">
              {isVendor ? "Files (you can select multiple PDFs)" : "File"}
            </Label>
            <Input id="file" type="file" ref={fileInputRef} accept=".pdf,.docx" multiple={isVendor} />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSubmit} disabled={uploading}>
            <Upload size={14} />
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
