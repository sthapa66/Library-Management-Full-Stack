import uuid
from datetime import datetime, timezone

from pydantic import EmailStr
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

from typing import Optional


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ============================================================================
# Library Management System Models
# ============================================================================

# BOOK models
class BookBase(SQLModel):
    isbn: str = Field(max_length=255)
    title: str = Field(max_length=255)


class BookCreate(BookBase):
    pass


class BookUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)


class Book(BookBase, table=True):
    isbn: str = Field(primary_key=True, max_length=255)

    book_authors: list["BookAuthor"] = Relationship(back_populates="book", cascade_delete=True)
    book_loans: list["BookLoan"] = Relationship(back_populates="book")


class BookPublic(BookBase):
    pass


class BooksPublic(SQLModel):
    data: list[BookPublic]
    count: int


# AUTHORS models
class AuthorBase(SQLModel):
    name: str = Field(max_length=255)


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)


class Author(AuthorBase, table=True):
    __tablename__ = "authors"

    author_id: int | None = Field(default=None, primary_key=True)

    book_authors: list["BookAuthor"] = Relationship(back_populates="author", cascade_delete=True)


class AuthorPublic(AuthorBase):
    author_id: int


class AuthorsPublic(SQLModel):
    data: list[AuthorPublic]
    count: int


# BOOK_AUTHORS models (junction table)
class BookAuthorBase(SQLModel):
    author_id: int
    isbn: str = Field(max_length=255)


class BookAuthorCreate(BookAuthorBase):
    pass


class BookAuthor(BookAuthorBase, table=True):
    __tablename__ = "book_authors"

    author_id: int = Field(foreign_key="authors.author_id", primary_key=True)
    isbn: str = Field(foreign_key="book.isbn", primary_key=True, max_length=255)

    author: Author | None = Relationship(back_populates="book_authors")
    book: Book | None = Relationship(back_populates="book_authors")


class BookAuthorPublic(BookAuthorBase):
    pass


class BookSearchResult(SQLModel):
    isbn: str
    title: str
    authors: str | None = None
    available: str  # 'IN' or 'OUT'

class BooksSearchPublic(SQLModel):
    data: list[BookSearchResult]
    count: int


# BORROWER models
class BorrowerBase(SQLModel):
    ssn: str | None = Field(default=None, max_length=255)
    bname: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=255)


class BorrowerCreate(BorrowerBase):
    pass


class BorrowerUpdate(BorrowerBase):
    pass


class Borrower(BorrowerBase, table=True):
    card_id: int | None = Field(default=None, primary_key=True)

    book_loans: list["BookLoan"] = Relationship(back_populates="borrower")


class BorrowerPublic(BorrowerBase):
    card_id: int


class BorrowersPublic(SQLModel):
    data: list[BorrowerPublic]
    count: int


# BOOK_LOANS models
class BookLoanBase(SQLModel):
    isbn: str = Field(max_length=255)
    card_id: int
    date_out: str | None = Field(default=None, max_length=255)
    due_date: str | None = Field(default=None, max_length=255)
    date_in: str | None = Field(default=None, max_length=255)


class BookLoanCreate(BookLoanBase):
    pass


class BookLoanUpdate(SQLModel):
    date_out: str | None = Field(default=None, max_length=255)
    due_date: str | None = Field(default=None, max_length=255)
    date_in: str | None = Field(default=None, max_length=255)


class BookLoan(BookLoanBase, table=True):
    __tablename__ = "book_loans"

    loan_id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(foreign_key="book.isbn", max_length=255)
    card_id: int = Field(foreign_key="borrower.card_id")

    book: Book | None = Relationship(back_populates="book_loans")
    borrower: Borrower | None = Relationship(back_populates="book_loans")
    fine: Optional["Fine"] = Relationship(back_populates="book_loan", cascade_delete=True)


class BookLoanPublic(BookLoanBase):
    loan_id: int


class BookLoansPublic(SQLModel):
    data: list[BookLoanPublic]
    count: int


# FINES models
class FineBase(SQLModel):
    fine_amt: float | None = None
    paid: bool = False


class FineCreate(FineBase):
    loan_id: int


class FineUpdate(SQLModel):
    fine_amt: float | None = None
    paid: bool | None = None


class Fine(FineBase, table=True):
    __tablename__ = "fines"

    loan_id: int = Field(foreign_key="book_loans.loan_id", primary_key=True)

    book_loan: BookLoan | None = Relationship(back_populates="fine")


class FinePublic(FineBase):
    loan_id: int


class FinesPublic(SQLModel):
    data: list[FinePublic]
    count: int
