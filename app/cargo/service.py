from sqlalchemy.orm import Session
from app.cargo import models, schemas

def get_cargo_by_id(db: Session, cargo_id: int):
    return db.query(models.Cargo).filter(models.Cargo.id == cargo_id).first()


def get_all_cargo(db: Session, status: schemas.CargoStatus | None = None):
    query = db.query(models.Cargo)
    if status:
        query = query.filter(models.Cargo.status == status)
    return query.all()


def upsert_cargo(db: Session, cargo_data: schemas.CargoCreate):
    db_cargo = db.query(models.Cargo).filter(models.Cargo.external_id == cargo_data.external_id).first()

    if db_cargo:
        for key, value in cargo_data.model_dump().items():
            setattr(db_cargo, key, value)
    else:
        db_cargo = models.Cargo(**cargo_data.model_dump())
        db.add(db_cargo)

    db.commit()
    db.refresh(db_cargo)
    return db_cargo
