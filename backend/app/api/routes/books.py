from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import col, or_, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Book,
    Author,
    BookAuthor,
    BookPublic,
    BooksPublic,
    BookLoan,
    BookSearchResult,
    BooksSearchPublic
)
from app.utils import generate_new_account_email, send_email
from sqlalchemy import func, case, exists, and_, or_


def get_books_search(
    session: SessionDep,
    query: str | None = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Book], int]:
    """Search books by title, ISBN, or author name"""

    if query:
        keyword = f"%{query.lower()}%"

        # Main query with aggregated authors and availability status
        statement = (
            select(
                Book.isbn,
                Book.title,
                func.string_agg(Author.name, ', ').label('authors'),
                case(
                    (
                        exists(
                            select(1)
                            .select_from(BookLoan)
                            .where(
                                and_(
                                    BookLoan.isbn == Book.isbn,
                                    BookLoan.date_in.is_(None)
                                )
                            )
                        ),
                        'OUT'
                    ),
                    else_='IN'
                ).label('available')
            )
            .select_from(Book)
            .join(BookAuthor, Book.isbn == BookAuthor.isbn, isouter=True)
            .join(Author, BookAuthor.author_id == Author.author_id, isouter=True)
            .where(
                or_(
                    func.lower(Book.isbn).like(keyword),
                    func.lower(Book.title).like(keyword),
                    func.lower(Author.name).like(keyword)
                )
            )
            .group_by(Book.isbn, Book.title)
            .order_by(Book.title)
        )
    else:
        # Query without search filter
        statement = (
            select(
                Book.isbn,
                Book.title,
                func.string_agg(Author.name, ', ').label('authors'),  # Changed from group_concat
                case(
                    (
                        exists(
                            select(1)
                            .select_from(BookLoan)
                            .where(
                                and_(
                                    BookLoan.isbn == Book.isbn,
                                    BookLoan.date_in.is_(None)
                                )
                            )
                        ),
                        'OUT'
                    ),
                    else_='IN'
                ).label('available')
            )
            .select_from(Book)
            .join(BookAuthor, Book.isbn == BookAuthor.isbn, isouter=True)
            .join(Author, BookAuthor.author_id == Author.author_id, isouter=True)
            .group_by(Book.isbn, Book.title)
            .order_by(Book.title)
        )

    # Get total count
    count_statement = select(func.count()).select_from(statement.alias())
    count = session.exec(count_statement).one()

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    results = session.exec(statement).all()

    return results, count


def create_book_with_author(
    session: SessionDep,
    isbn: str,
    title: str,
    author_name: str
) -> Book:
    """Create a new book with an author (creates author if doesn't exist)"""
    # Check if book already exists
    existing_book = session.get(Book, isbn)
    if existing_book:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")

    # Create or get author
    author_statement = select(Author).where(Author.name == author_name)
    author = session.exec(author_statement).first()

    if not author:
        author = Author(name=author_name)
        session.add(author)
        session.commit()
        session.refresh(author)

    # Create book
    book = Book(isbn=isbn, title=title)
    session.add(book)
    session.commit()
    session.refresh(book)

    # Create book-author relationship
    book_author = BookAuthor(isbn=isbn, author_id=author.author_id)
    session.add(book_author)
    session.commit()

    return book


def delete_book_by_isbn(session: SessionDep, isbn: str) -> Book:
    """Delete a book by ISBN"""
    book = session.get(Book, isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # SQLModel will handle cascade delete for book_authors
    session.delete(book)
    session.commit()

    return book


# tags are labels that appear in the auto‑generated OpenAPI/Swagger UI.
router = APIRouter(prefix="/books", tags=["books"])


@router.get("/search", response_model=BooksSearchPublic)
def search_books(
    session: SessionDep,
    query: str | None = Query(default=None, description="Search by title, ISBN, or author name"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100)
):
    """
    Search for books by title, ISBN, or author name.
    Returns paginated results with author names and availability status.
    """
    results, count = get_books_search(session, query=query, skip=skip, limit=limit)

    # Convert results to response model
    books = [
        BookSearchResult(
            isbn=row.isbn,
            title=row.title,
            authors=row.authors,
            available=row.available
        )
        for row in results
    ]

    return BooksSearchPublic(data=books, count=count)


@router.post("/", dependencies=[Depends(get_current_active_superuser)], response_model=BookPublic, status_code=201)
def create_book(
    isbn: str,
    title: str,
    author_name: str,
    session: SessionDep,
):
    """
    Create a new book with an author.
    If the author doesn't exist, it will be created automatically.
    """
    book = create_book_with_author(
        session=session,
        isbn=isbn,
        title=title,
        author_name=author_name
    )
    return book


@router.delete("/{isbn}", dependencies=[Depends(get_current_active_superuser)], response_model=BookPublic)
def delete_book(
    isbn: str,
    session: SessionDep,
):
    """
    Delete a book by ISBN.
    This will also delete associated book-author relationships.
    """
    book = delete_book_by_isbn(session, isbn)
    return book
