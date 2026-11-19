from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One branch office (for example Dadar).
class Office(Base):
    __tablename__ = "office"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
