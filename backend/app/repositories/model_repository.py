from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.model import Model, ModelStatus


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, model: Model) -> Model:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_by_id(self, model_id: str) -> Model | None:
        return self.db.get(Model, model_id)

    def list_for_user(
        self, user_id: str, search: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Model], int]:
        stmt = select(Model).where(Model.user_id == user_id)
        if search:
            stmt = stmt.where(Model.name.ilike(f"%{search}%"))
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        stmt = stmt.order_by(Model.created_at.desc()).limit(limit).offset(offset)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total

    def update_status(self, model: Model, status: ModelStatus, error: str | None = None) -> Model:
        model.status = status
        model.validation_error = error
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model: Model) -> None:
        self.db.delete(model)
        self.db.commit()

    def count_for_user(self, user_id: str) -> int:
        return self.db.execute(
            select(func.count()).select_from(Model).where(Model.user_id == user_id)
        ).scalar_one()
