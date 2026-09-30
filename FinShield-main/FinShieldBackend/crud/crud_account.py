from sqlalchemy.orm import Session
from typing import List, Optional
from models.account import Account
from schemas.account import AccountCreate, AccountUpdate


def create_user_account(db: Session, account_in: AccountCreate, user_id: int) -> Account:
    db_account = Account(
        user_id=user_id,
        account_number=account_in.account_number,
        bank_name=account_in.bank_name,
        account_name=account_in.account_name,
        balance=account_in.initial_balance,
        account_type=account_in.account_type,
        status=account_in.status,
        is_active=True
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def get_user_accounts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Account]:
    return db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(limit).all()


def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
    return db.query(Account).filter(Account.id == account_id).first()


def get_account_by_number(db: Session, account_number: str) -> Optional[Account]:
    return db.query(Account).filter(Account.account_number == account_number).first()


def update_account(db: Session, db_account: Account, account_in: AccountUpdate) -> Account:
    update_data = account_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_account(db: Session, account_id: int) -> bool:
    db_account = get_account_by_id(db, account_id)
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False


def deactivate_account(db: Session, db_account: Account) -> Account:
    db_account.is_active = False
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_account_balance(db: Session, db_account: Account, amount: int) -> Account:
    db_account.balance += amount
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account
