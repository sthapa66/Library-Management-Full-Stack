import { type ColumnDef } from "@tanstack/react-table"
// import { Trash2 } from "lucide-react"

import { type BookPublic } from "@/client"
// import { Button } from "@/components/ui/button"
import DeleteBook from "@/components/Books/DeleteBook"

export const columns: ColumnDef<BookPublic>[] = [
  {
    accessorKey: "isbn",
    header: "ISBN",
  },
  {
    accessorKey: "title",
    header: "Title",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const book = row.original

      return (
        <div className="flex justify-end">
          <DeleteBook book={book} />
        </div>
      )
    },
  },
]