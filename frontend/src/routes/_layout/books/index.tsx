import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense, useState } from "react"
import { Link } from "@tanstack/react-router"

import { BooksService, BookSearchResult } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import PendingBooks from "@/components/Pending/PendingBooks"
import useAuth from "@/hooks/useAuth"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search } from "lucide-react"
import { ColumnDef } from "@tanstack/react-table"
import DeleteBook from "@/components/Books/DeleteBook"

// Updated columns for the new data structure
const searchColumns: ColumnDef<BookSearchResult>[] = [
  {
    accessorKey: "isbn",
    header: "ISBN",
  },
  {
    accessorKey: "title",
    header: "Title",
  },
  {
    accessorKey: "authors",
    header: "Authors",
    cell: ({ row }) => row.original.authors || "No authors",
  },
  {
    accessorKey: "available",
    header: "Status",
    cell: ({ row }) => (
      <span
        className={
          row.original.available === "IN"
            ? "text-green-600 font-medium"
            : "text-red-600 font-medium"
        }
      >
        {row.original.available === "IN" ? "Available" : "Checked Out"}
      </span>
    ),
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

function getBooksQueryOptions(query: string) {
  return {
    queryFn: () =>
      BooksService.searchBooks({ query: query || undefined, skip: 0, limit: 100 }),
    queryKey: ["books", query],
  }
}

export const Route = createFileRoute("/_layout/books/")({
  component: Books,
  head: () => ({
    meta: [
      {
        title: "Books - Example Library",
      },
    ],
  }),
})

function BooksTableContent({ query }: { query: string }) {
  const { data: books } = useSuspenseQuery(getBooksQueryOptions(query))

  return <DataTable columns={searchColumns} data={books.data} />
}

function BooksTable({ query }: { query: string }) {
  return (
    <Suspense fallback={<PendingBooks />}>
      <BooksTableContent query={query} />
    </Suspense>
  )
}

function Books() {
  const { user } = useAuth()
  const [searchQuery, setSearchQuery] = useState("")
  const [activeQuery, setActiveQuery] = useState("")

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setActiveQuery(searchQuery)
  }

  const handleClear = () => {
    setSearchQuery("")
    setActiveQuery("")
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Books</h1>
          <p className="text-muted-foreground">
            Search and manage book catalog
          </p>
        </div>
        {user?.is_superuser && (
          <Link to="/books/add">
            <Button>Add Book</Button>
          </Link>
        )}
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by title, ISBN, or author name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit">Search</Button>
        {activeQuery && (
          <Button type="button" variant="outline" onClick={handleClear}>
            Clear
          </Button>
        )}
      </form>

      <BooksTable query={activeQuery} />
    </div>
  )
}