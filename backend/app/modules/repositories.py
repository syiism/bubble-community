from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from .user import User
from .bubble import Bubble
from .user_current_bubble import UserCurrentBubble
from .imported_bubble import ImportedBubble
from .user_favorite import UserFavorite
from .session_model import Session


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_author_name(db: Session, author_name: str) -> User | None:
        return db.query(User).filter(User.author_name == author_name).first()

    @staticmethod
    def create(db: Session, user_id: int, username: str, avatar_url: str | None = None) -> User:
        user = User(id=user_id, username=username, avatar_url=avatar_url)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_author_name(db: Session, user_id: int, author_name: str | None) -> None:
        db.query(User).filter(User.id == user_id).update({"author_name": author_name})
        db.query(Bubble).filter(Bubble.user_id == user_id).update({"author_name": author_name or ""})
        db.commit()


class BubbleRepository:
    @staticmethod
    def get_by_id(db: Session, bubble_id: int) -> Bubble | None:
        return db.query(Bubble).filter(Bubble.id == bubble_id).first()

    @staticmethod
    def get_by_share_code(db: Session, share_code: str) -> Bubble | None:
        return db.query(Bubble).filter(Bubble.share_code == share_code).first()

    @staticmethod
    def get_official_bubbles(db: Session) -> list[Bubble]:
        return db.query(Bubble).filter(Bubble.is_official == True).all()

    @staticmethod
    def get_official_first(db: Session) -> Bubble | None:
        return db.query(Bubble).filter(Bubble.is_official == True).first()

    @staticmethod
    def get_user_bubbles(db: Session, user_id: int) -> list[Bubble]:
        return db.query(Bubble).filter(Bubble.user_id == user_id).all()

    @staticmethod
    def get_public_bubbles(db: Session) -> list[Bubble]:
        return db.query(Bubble).filter(Bubble.is_public == True).all()

    @staticmethod
    def get_visible_bubbles(db: Session, user_id: int) -> list[Bubble]:
        imported_ids = [ib.bubble_id for ib in db.query(ImportedBubble).filter(ImportedBubble.user_id == user_id).all()]
        current_bubble_id = db.query(UserCurrentBubble.bubble_id).filter(UserCurrentBubble.user_id == user_id).scalar()

        query = db.query(Bubble).filter(
            or_(
                Bubble.is_official == True,
                Bubble.is_public == True,
                Bubble.user_id == user_id,
                Bubble.id.in_(imported_ids),
            )
        )

        if current_bubble_id:
            existing_ids = {b.id for b in query.all()}
            if current_bubble_id not in existing_ids:
                current_bubble = db.query(Bubble).filter(Bubble.id == current_bubble_id).first()
                if current_bubble:
                    result = query.all()
                    result.append(current_bubble)
                    return result

        return query.order_by(Bubble.is_official.desc(), Bubble.id.desc()).all()

    @staticmethod
    def get_bubble_uses(db: Session, bubble_id: int) -> int:
        return db.query(func.count(UserCurrentBubble.user_id)).filter(UserCurrentBubble.bubble_id == bubble_id).scalar()

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        name: str,
        description: str,
        svg_template: str,
        color: str = "",
        text_color: str = "",
        is_public: bool = False,
        author_name: str = "",
    ) -> Bubble:
        bubble = Bubble(
            user_id=user_id,
            name=name,
            description=description,
            svg_template=svg_template,
            color=color,
            text_color=text_color,
            is_public=is_public,
            author_name=author_name,
        )
        db.add(bubble)
        db.commit()
        db.refresh(bubble)
        return bubble

    @staticmethod
    def update(db: Session, bubble: Bubble, **kwargs) -> Bubble:
        for key, value in kwargs.items():
            setattr(bubble, key, value)
        db.commit()
        db.refresh(bubble)
        return bubble

    @staticmethod
    def delete(db: Session, bubble_id: int) -> None:
        db.query(UserCurrentBubble).filter(UserCurrentBubble.bubble_id == bubble_id).delete()
        db.query(ImportedBubble).filter(ImportedBubble.bubble_id == bubble_id).delete()
        db.query(UserFavorite).filter(UserFavorite.bubble_id == bubble_id).delete()
        db.query(Bubble).filter(Bubble.id == bubble_id).delete()
        db.commit()

    @staticmethod
    def count_official(db: Session) -> int:
        return db.query(func.count(Bubble.id)).filter(Bubble.is_official == True).scalar()

    @staticmethod
    def create_official(
        db: Session,
        name: str,
        description: str,
        svg_template: str,
        color: str = "",
        text_color: str = "",
        author_name: str = "",
    ) -> Bubble:
        bubble = Bubble(
            name=name,
            description=description,
            svg_template=svg_template,
            color=color,
            text_color=text_color,
            is_public=True,
            is_official=True,
            author_name=author_name,
        )
        db.add(bubble)
        return bubble


class UserCurrentBubbleRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> UserCurrentBubble | None:
        return db.query(UserCurrentBubble).filter(UserCurrentBubble.user_id == user_id).first()

    @staticmethod
    def set_current(db: Session, user_id: int, bubble_id: int) -> None:
        existing = db.query(UserCurrentBubble).filter(UserCurrentBubble.user_id == user_id).first()
        if existing:
            existing.bubble_id = bubble_id
        else:
            db.add(UserCurrentBubble(user_id=user_id, bubble_id=bubble_id))
        db.commit()


class ImportedBubbleRepository:
    @staticmethod
    def get_imported_ids(db: Session, user_id: int) -> set[int]:
        return {ib.bubble_id for ib in db.query(ImportedBubble).filter(ImportedBubble.user_id == user_id).all()}

    @staticmethod
    def is_imported(db: Session, user_id: int, bubble_id: int) -> bool:
        return db.query(ImportedBubble).filter(
            and_(ImportedBubble.user_id == user_id, ImportedBubble.bubble_id == bubble_id)
        ).first() is not None

    @staticmethod
    def import_bubble(db: Session, user_id: int, bubble_id: int) -> None:
        if not ImportedBubbleRepository.is_imported(db, user_id, bubble_id):
            db.add(ImportedBubble(user_id=user_id, bubble_id=bubble_id))
            db.commit()


class UserFavoriteRepository:
    @staticmethod
    def get_favorite_ids(db: Session, user_id: int) -> set[int]:
        return {uf.bubble_id for uf in db.query(UserFavorite).filter(UserFavorite.user_id == user_id).all()}

    @staticmethod
    def is_favorited(db: Session, user_id: int, bubble_id: int) -> bool:
        return db.query(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.bubble_id == bubble_id)
        ).first() is not None

    @staticmethod
    def set_favorite(db: Session, user_id: int, bubble_id: int, favorite: bool) -> None:
        if favorite:
            if not UserFavoriteRepository.is_favorited(db, user_id, bubble_id):
                db.add(UserFavorite(user_id=user_id, bubble_id=bubble_id))
        else:
            db.query(UserFavorite).filter(
                and_(UserFavorite.user_id == user_id, UserFavorite.bubble_id == bubble_id)
            ).delete()
        db.commit()

    @staticmethod
    def count_favorites(db: Session, user_id: int) -> int:
        return db.query(func.count(UserFavorite.bubble_id)).filter(UserFavorite.user_id == user_id).scalar()


class SessionRepository:
    SESSION_EXPIRE = timedelta(hours=2)

    @staticmethod
    def create(db: Session, session_id: str, user_id: int, username: str) -> Session:
        expires_at = datetime.now() + SessionRepository.SESSION_EXPIRE
        session = Session(id=session_id, user_id=user_id, username=username, expires_at=expires_at)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get(db: Session, session_id: str) -> Session | None:
        return db.query(Session).filter(Session.id == session_id).first()

    @staticmethod
    def delete(db: Session, session_id: str) -> None:
        db.query(Session).filter(Session.id == session_id).delete()
        db.commit()

    @staticmethod
    def is_valid(db: Session, session: Session) -> bool:
        if not session:
            return False
        return datetime.now() < session.expires_at

    @staticmethod
    def refresh_expiry(db: Session, session: Session) -> None:
        session.expires_at = datetime.now() + SessionRepository.SESSION_EXPIRE
        db.commit()

    @staticmethod
    def cleanup_expired(db: Session) -> None:
        db.query(Session).filter(Session.expires_at < datetime.now()).delete()
        db.commit()
