import { useQuery } from "@tanstack/react-query"
import { orgApi } from "@/api/org"

export function useOrgMe() {
  return useQuery({
    queryKey: ["org", "me"],
    queryFn: () => orgApi.me(),
  })
}
