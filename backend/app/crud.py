import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate
from app.models import (
    Author,
    AuthorCreate,
    AuthorUpdate,
    Book,
    BookAuthor,
    BookAuthorCreate,
    BookCreate,
    BookLoan,
    BookLoanCreate,
    BookLoanUpdate,
    BookUpdate,
    Borrower,
    BorrowerCreate,
    BorrowerUpdate,
    Fine,
    FineCreate,
    FineUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ============================================================================
# BOOK CRUD functions
# ============================================================================


def create_book(*, session: Session, book_in: BookCreate) -> Book:
    db_book = Book.model_validate(book_in)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


def get_book_by_isbn(*, session: Session, isbn: str) -> Book | None:
    statement = select(Book).where(Book.isbn == isbn)
    book = session.exec(statement).first()
    return book


def get_books(*, session: Session, skip: int = 0, limit: int = 100) -> list[Book]:
    statement = select(Book).offset(skip).limit(limit)
    books = session.exec(statement).all()
    return list(books)


def update_book(*, session: Session, db_book: Book, book_in: BookUpdate) -> Book:
    book_data = book_in.model_dump(exclude_unset=True)
    db_book.sqlmodel_update(book_data)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


def delete_book(*, session: Session, db_book: Book) -> None:
    session.delete(db_book)
    session.commit()


# ============================================================================
# AUTHOR CRUD functions
# ============================================================================


def create_author(*, session: Session, author_in: AuthorCreate) -> Author:
    db_author = Author.model_validate(author_in)
    session.add(db_author)
    session.commit()
    session.refresh(db_author)
    return db_author


def get_author_by_id(*, session: Session, author_id: int) -> Author | None:
    statement = select(Author).where(Author.author_id == author_id)
    author = session.exec(statement).first()
    return author


def get_authors(*, session: Session, skip: int = 0, limit: int = 100) -> list[Author]:
    statement = select(Author).offset(skip).limit(limit)
    authors = session.exec(statement).all()
    return list(authors)


def get_authors_by_name(*, session: Session, name: str) -> list[Author]:
    statement = select(Author).where(Author.name.ilike(f"%{name}%"))  # type: ignore
    authors = session.exec(statement).all()
    return list(authors)


def update_author(*, session: Session, db_author: Author, author_in: AuthorUpdate) -> Author:
    author_data = author_in.model_dump(exclude_unset=True)
    db_author.sqlmodel_update(author_data)
    session.add(db_author)
    session.commit()
    session.refresh(db_author)
    return db_author


def delete_author(*, session: Session, db_author: Author) -> None:
    session.delete(db_author)
    session.commit()


# ============================================================================
# BOOK_AUTHOR CRUD functions
# ============================================================================


def create_book_author(*, session: Session, book_author_in: BookAuthorCreate) -> BookAuthor:
    db_book_author = BookAuthor.model_validate(book_author_in)
    session.add(db_book_author)
    session.commit()
    session.refresh(db_book_author)
    return db_book_author


def get_book_author(*, session: Session, author_id: int, isbn: str) -> BookAuthor | None:
    statement = select(BookAuthor).where(
        BookAuthor.author_id == author_id, BookAuthor.isbn == isbn
    )
    book_author = session.exec(statement).first()
    return book_author


def get_authors_by_book(*, session: Session, isbn: str) -> list[Author]:
    statement = (
        select(Author)
        .join(BookAuthor)
        .where(BookAuthor.isbn == isbn)
    )
    authors = session.exec(statement).all()
    return list(authors)


def get_books_by_author(*, session: Session, author_id: int) -> list[Book]:
    statement = (
        select(Book)
        .join(BookAuthor)
        .where(BookAuthor.author_id == author_id)
    )
    books = session.exec(statement).all()
    return list(books)


def delete_book_author(*, session: Session, db_book_author: BookAuthor) -> None:
    session.delete(db_book_author)
    session.commit()


# ============================================================================
# BORROWER CRUD functions
# ============================================================================


def create_borrower(*, session: Session, borrower_in: BorrowerCreate) -> Borrower:
    db_borrower = Borrower.model_validate(borrower_in)
    session.add(db_borrower)
    session.commit()
    session.refresh(db_borrower)
    return db_borrower


def get_borrower_by_id(*, session: Session, card_id: int) -> Borrower | None:
    statement = select(Borrower).where(Borrower.card_id == card_id)
    borrower = session.exec(statement).first()
    return borrower


def get_borrower_by_ssn(*, session: Session, ssn: str) -> Borrower | None:
    statement = select(Borrower).where(Borrower.ssn == ssn)
    borrower = session.exec(statement).first()
    return borrower


def get_borrowers(*, session: Session, skip: int = 0, limit: int = 100) -> list[Borrower]:
    statement = select(Borrower).offset(skip).limit(limit)
    borrowers = session.exec(statement).all()
    return list(borrowers)


def search_borrowers_by_name(*, session: Session, name: str) -> list[Borrower]:
    statement = select(Borrower).where(Borrower.bname.ilike(f"%{name}%"))  # type: ignore
    borrowers = session.exec(statement).all()
    return list(borrowers)


def update_borrower(
    *, session: Session, db_borrower: Borrower, borrower_in: BorrowerUpdate
) -> Borrower:
    borrower_data = borrower_in.model_dump(exclude_unset=True)
    db_borrower.sqlmodel_update(borrower_data)
    session.add(db_borrower)
    session.commit()
    session.refresh(db_borrower)
    return db_borrower


def delete_borrower(*, session: Session, db_borrower: Borrower) -> None:
    session.delete(db_borrower)
    session.commit()


# ============================================================================
# BOOK_LOAN CRUD functions
# ============================================================================


def create_book_loan(*, session: Session, book_loan_in: BookLoanCreate) -> BookLoan:
    db_book_loan = BookLoan.model_validate(book_loan_in)
    session.add(db_book_loan)
    session.commit()
    session.refresh(db_book_loan)
    return db_book_loan


def get_book_loan_by_id(*, session: Session, loan_id: int) -> BookLoan | None:
    statement = select(BookLoan).where(BookLoan.loan_id == loan_id)
    book_loan = session.exec(statement).first()
    return book_loan


def get_book_loans(*, session: Session, skip: int = 0, limit: int = 100) -> list[BookLoan]:
    statement = select(BookLoan).offset(skip).limit(limit)
    book_loans = session.exec(statement).all()
    return list(book_loans)


def get_active_loans_by_borrower(*, session: Session, card_id: int) -> list[BookLoan]:
    """Get all active (not returned) loans for a borrower"""
    statement = select(BookLoan).where(
        BookLoan.card_id == card_id, BookLoan.date_in == None  # noqa: E711
    )
    book_loans = session.exec(statement).all()
    return list(book_loans)


def get_active_loans_by_book(*, session: Session, isbn: str) -> list[BookLoan]:
    """Get all active (not returned) loans for a book"""
    statement = select(BookLoan).where(
        BookLoan.isbn == isbn, BookLoan.date_in == None  # noqa: E711
    )
    book_loans = session.exec(statement).all()
    return list(book_loans)


def get_overdue_loans(*, session: Session) -> list[BookLoan]:
    """Get all overdue loans (due_date passed and not returned)"""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    statement = select(BookLoan).where(
        BookLoan.date_in == None,  # noqa: E711
        str(BookLoan.due_date) < today
    )
    book_loans = session.exec(statement).all()
    return list(book_loans)


def update_book_loan(
    *, session: Session, db_book_loan: BookLoan, book_loan_in: BookLoanUpdate
) -> BookLoan:
    book_loan_data = book_loan_in.model_dump(exclude_unset=True)
    db_book_loan.sqlmodel_update(book_loan_data)
    session.add(db_book_loan)
    session.commit()
    session.refresh(db_book_loan)
    return db_book_loan


def return_book(*, session: Session, db_book_loan: BookLoan, date_in: str) -> BookLoan:
    """Mark a book as returned"""
    db_book_loan.date_in = date_in
    session.add(db_book_loan)
    session.commit()
    session.refresh(db_book_loan)
    return db_book_loan


def delete_book_loan(*, session: Session, db_book_loan: BookLoan) -> None:
    session.delete(db_book_loan)
    session.commit()


# ============================================================================
# FINE CRUD functions
# ============================================================================


def create_fine(*, session: Session, fine_in: FineCreate) -> Fine:
    db_fine = Fine.model_validate(fine_in)
    session.add(db_fine)
    session.commit()
    session.refresh(db_fine)
    return db_fine


def get_fine_by_loan_id(*, session: Session, loan_id: int) -> Fine | None:
    statement = select(Fine).where(Fine.loan_id == loan_id)
    fine = session.exec(statement).first()
    return fine


def get_fines(*, session: Session, skip: int = 0, limit: int = 100) -> list[Fine]:
    statement = select(Fine).offset(skip).limit(limit)
    fines = session.exec(statement).all()
    return list(fines)


def get_unpaid_fines(*, session: Session) -> list[Fine]:
    """Get all unpaid fines"""
    statement = select(Fine).where(Fine.paid == False)  # noqa: E712
    fines = session.exec(statement).all()
    return list(fines)


def get_fines_by_borrower(*, session: Session, card_id: int) -> list[Fine]:
    """Get all fines for a borrower"""
    statement = (
        select(Fine)
        .join(BookLoan)
        .where(BookLoan.card_id == card_id)
    )
    fines = session.exec(statement).all()
    return list(fines)


def update_fine(*, session: Session, db_fine: Fine, fine_in: FineUpdate) -> Fine:
    fine_data = fine_in.model_dump(exclude_unset=True)
    db_fine.sqlmodel_update(fine_data)
    session.add(db_fine)
    session.commit()
    session.refresh(db_fine)
    return db_fine


def mark_fine_as_paid(*, session: Session, db_fine: Fine) -> Fine:
    """Mark a fine as paid"""
    db_fine.paid = True
    session.add(db_fine)
    session.commit()
    session.refresh(db_fine)
    return db_fine


def delete_fine(*, session: Session, db_fine: Fine) -> None:
    session.delete(db_fine)
    session.commit()
