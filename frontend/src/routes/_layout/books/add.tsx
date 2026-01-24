import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

import { BooksService, UsersService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { useToast } from "@/hooks/useToast"
import { ArrowLeft } from "lucide-react"
import { Link } from "@tanstack/react-router"

const bookSchema = z.object({
  isbn: z.string().min(1, "ISBN is required"),
  title: z.string().min(1, "Title is required"),
  authorName: z.string().min(1, "Author name is required"),
})

type BookFormValues = z.infer<typeof bookSchema>

export const Route = createFileRoute("/_layout/books/add")({
  component: AddBook,
  beforeLoad: async () => {
    const user = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({
        to: "/books",
      })
    }
  },
})

function AddBook() {
  const { toast } = useToast()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const form = useForm<BookFormValues>({
    resolver: zodResolver(bookSchema),
    defaultValues: {
      isbn: "",
      title: "",
      authorName: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: BookFormValues) =>
      BooksService.createBook({
        isbn: data.isbn,
        title: data.title,
        authorName: data.authorName,
      }),
    onSuccess: () => {
      toast({
        title: "Book created",
        description: "The book has been added successfully.",
      })
      queryClient.invalidateQueries({ queryKey: ["books"] })
      navigate({ to: "/books" })
    },
    onError: (error: any) => {
      toast({
        title: "Error creating book",
        description: error.message || "An error occurred while creating the book.",
        variant: "destructive",
      })
    },
  })

  const onSubmit = (data: BookFormValues) => {
    mutation.mutate(data)
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <Link to="/books">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Books
          </Button>
        </Link>
        <h1 className="text-2xl font-bold tracking-tight">Add Book</h1>
        <p className="text-muted-foreground">
          Add a new book to the catalog
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <FormField
            control={form.control}
            name="isbn"
            render={({ field }) => (
              <FormItem>
                <FormLabel>ISBN</FormLabel>
                <FormControl>
                  <Input placeholder="978-0-123456-78-9" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Title</FormLabel>
                <FormControl>
                  <Input placeholder="Book title" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="authorName"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Author Name</FormLabel>
                <FormControl>
                  <Input placeholder="Author full name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex gap-2">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Adding..." : "Add Book"}
            </Button>
            <Link to="/books">
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </Link>
          </div>
        </form>
      </Form>
    </div>
  )
}