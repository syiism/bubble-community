from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, select, delete, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from .user import User
from .bubble import Bubble
from .user_current_bubble import UserCurrentBubble
from .imported_bubble import ImportedBubble
from .user_favorite import UserFavorite
from .session_model import Session
from ..password_util import hash_password


class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_author_name(db: AsyncSession, author_name: str) -> User | None:
        result = await db.execute(select(User).filter(User.author_name == author_name))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_id: int, username: str, avatar_url: str | None = None) -> User:
        user = User(id=user_id, username=username, avatar_url=avatar_url)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_or_create(db: AsyncSession, user_id: int, username: str, avatar_url: str | None = None) -> User:
        """原子化 get-or-create，消除并发创建竞态。"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

        insert_stmt = mysql_insert(User).values(
            id=user_id, username=username, avatar_url=avatar_url
        ).on_duplicate_key_update(
            id=mysql_insert(User).inserted.id  # no-op, 仅防 duplicate key 报错
        )
        await db.execute(insert_stmt)
        await db.commit()

        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalar_one()

    @staticmethod
    async def update(db: AsyncSession, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_author_name(db: AsyncSession, user_id: int, author_name: str | None) -> None:
        await db.execute(update(User).where(User.id == user_id).values({"author_name": author_name}))
        await db.execute(update(Bubble).where(Bubble.user_id == user_id).values({"author_name": author_name or ""}))
        await db.commit()

    @staticmethod
    async def update_password(db: AsyncSession, user_id: int, plain_password: str) -> None:
        hashed = hash_password(plain_password)
        await db.execute(update(User).where(User.id == user_id).values({"password": hashed}))
        await db.commit()


class BubbleRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, bubble_id: int) -> Bubble | None:
        result = await db.execute(select(Bubble).filter(Bubble.id == bubble_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_share_code(db: AsyncSession, share_code: str) -> Bubble | None:
        result = await db.execute(select(Bubble).filter(Bubble.share_code == share_code))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_official_bubbles(db: AsyncSession) -> list[Bubble]:
        result = await db.execute(select(Bubble).filter(Bubble.is_official == True))
        return result.scalars().all()

    @staticmethod
    async def get_official_first(db: AsyncSession) -> Bubble | None:
        result = await db.execute(select(Bubble).filter(Bubble.is_official == True))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_bubbles(db: AsyncSession, user_id: int) -> list[Bubble]:
        result = await db.execute(select(Bubble).filter(Bubble.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def get_public_bubbles(db: AsyncSession) -> list[Bubble]:
        result = await db.execute(select(Bubble).filter(Bubble.is_public == True))
        return result.scalars().all()

    @staticmethod
    async def get_visible_bubbles(db: AsyncSession, user_id: int) -> list[Bubble]:
        imported_result = await db.execute(select(ImportedBubble.bubble_id).filter(ImportedBubble.user_id == user_id))
        imported_ids = [row[0] for row in imported_result.all()]

        current_result = await db.execute(select(UserCurrentBubble.bubble_id).filter(UserCurrentBubble.user_id == user_id))
        current_bubble_id = current_result.scalar()

        query = select(Bubble).filter(
            or_(
                Bubble.is_official == True,
                Bubble.is_public == True,
                Bubble.user_id == user_id,
                Bubble.id.in_(imported_ids),
            )
        )

        result = await db.execute(query)
        bubbles = result.scalars().all()

        if current_bubble_id:
            existing_ids = {b.id for b in bubbles}
            if current_bubble_id not in existing_ids:
                current_result = await db.execute(select(Bubble).filter(Bubble.id == current_bubble_id))
                current_bubble = current_result.scalar_one_or_none()
                if current_bubble:
                    bubbles.append(current_bubble)

        return sorted(bubbles, key=lambda x: (-x.is_official, -x.id))

    @staticmethod
    async def get_bubble_uses(db: AsyncSession, bubble_id: int) -> int:
        result = await db.execute(select(func.count(UserCurrentBubble.user_id)).filter(UserCurrentBubble.bubble_id == bubble_id))
        return result.scalar()

    @staticmethod
    async def get_bubble_uses_batch(db: AsyncSession, bubble_ids: list[int]) -> dict[int, int]:
        if not bubble_ids:
            return {}
        result = await db.execute(
            select(
                UserCurrentBubble.bubble_id,
                func.count(UserCurrentBubble.user_id).label("count")
            )
            .filter(UserCurrentBubble.bubble_id.in_(bubble_ids))
            .group_by(UserCurrentBubble.bubble_id)
        )
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def create(
        db: AsyncSession,
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
        await db.commit()
        await db.refresh(bubble)
        return bubble

    @staticmethod
    async def update(db: AsyncSession, bubble: Bubble, **kwargs) -> Bubble:
        for key, value in kwargs.items():
            setattr(bubble, key, value)
        await db.commit()
        await db.refresh(bubble)
        return bubble

    @staticmethod
    async def delete(db: AsyncSession, bubble_id: int) -> None:
        await db.execute(delete(UserCurrentBubble).where(UserCurrentBubble.bubble_id == bubble_id))
        await db.execute(delete(ImportedBubble).where(ImportedBubble.bubble_id == bubble_id))
        await db.execute(delete(UserFavorite).where(UserFavorite.bubble_id == bubble_id))
        await db.execute(delete(Bubble).where(Bubble.id == bubble_id))
        await db.commit()

    @staticmethod
    async def count_official(db: AsyncSession) -> int:
        result = await db.execute(select(func.count(Bubble.id)).filter(Bubble.is_official == True))
        return result.scalar()

    @staticmethod
    async def create_official(
        db: AsyncSession,
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
    async def get_by_user_id(db: AsyncSession, user_id: int) -> UserCurrentBubble | None:
        result = await db.execute(select(UserCurrentBubble).filter(UserCurrentBubble.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def set_current(db: AsyncSession, user_id: int, bubble_id: int) -> None:
        stmt = mysql_insert(UserCurrentBubble).values(
            user_id=user_id, bubble_id=bubble_id
        ).on_duplicate_key_update(
            bubble_id=bubble_id,
        )
        await db.execute(stmt)
        await db.commit()


class ImportedBubbleRepository:
    @staticmethod
    async def get_imported_ids(db: AsyncSession, user_id: int) -> set[int]:
        result = await db.execute(select(ImportedBubble.bubble_id).filter(ImportedBubble.user_id == user_id))
        return {row[0] for row in result.all()}

    @staticmethod
    async def is_imported(db: AsyncSession, user_id: int, bubble_id: int) -> bool:
        result = await db.execute(select(ImportedBubble).filter(
            and_(ImportedBubble.user_id == user_id, ImportedBubble.bubble_id == bubble_id)
        ))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def import_bubble(db: AsyncSession, user_id: int, bubble_id: int) -> None:
        stmt = mysql_insert(ImportedBubble).values(
            user_id=user_id, bubble_id=bubble_id
        ).on_duplicate_key_update(
            user_id=mysql_insert(ImportedBubble).inserted.user_id,  # no-op，防重复
        )
        await db.execute(stmt)
        await db.commit()


class UserFavoriteRepository:
    @staticmethod
    async def get_favorite_ids(db: AsyncSession, user_id: int) -> set[int]:
        result = await db.execute(select(UserFavorite.bubble_id).filter(UserFavorite.user_id == user_id))
        return {row[0] for row in result.all()}

    @staticmethod
    async def is_favorited(db: AsyncSession, user_id: int, bubble_id: int) -> bool:
        result = await db.execute(select(UserFavorite).filter(
            and_(UserFavorite.user_id == user_id, UserFavorite.bubble_id == bubble_id)
        ))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def set_favorite(db: AsyncSession, user_id: int, bubble_id: int, favorite: bool) -> None:
        if favorite:
            stmt = mysql_insert(UserFavorite).values(
                user_id=user_id, bubble_id=bubble_id
            ).on_duplicate_key_update(
                user_id=mysql_insert(UserFavorite).inserted.user_id,  # no-op，防重复
            )
            await db.execute(stmt)
        else:
            await db.execute(delete(UserFavorite).where(
                and_(UserFavorite.user_id == user_id, UserFavorite.bubble_id == bubble_id)
            ))
        await db.commit()

    @staticmethod
    async def count_favorites(db: AsyncSession, user_id: int) -> int:
        result = await db.execute(select(func.count(UserFavorite.bubble_id)).filter(UserFavorite.user_id == user_id))
        return result.scalar()


class SessionRepository:
    SESSION_EXPIRE = timedelta(hours=2)

    @staticmethod
    async def create(db: AsyncSession, session_id: str, user_id: int, username: str) -> Session:
        expires_at = datetime.now() + SessionRepository.SESSION_EXPIRE
        session = Session(id=session_id, user_id=user_id, username=username, expires_at=expires_at)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get(db: AsyncSession, session_id: str) -> Session | None:
        result = await db.execute(select(Session).options(load_only(Session.id, Session.user_id, Session.username, Session.expires_at)).filter(Session.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_update(db: AsyncSession, session_id: str) -> Session | None:
        """带行锁读取 session，防止并发刷新/删除竞态。"""
        result = await db.execute(
            select(Session)
            .options(load_only(Session.id, Session.user_id, Session.username, Session.expires_at))
            .filter(Session.id == session_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(db: AsyncSession, session_id: str) -> None:
        await db.execute(delete(Session).where(Session.id == session_id))
        await db.commit()

    @staticmethod
    def is_valid(session: Session) -> bool:
        if not session:
            return False
        return datetime.now() < session.expires_at

    @staticmethod
    async def refresh_expiry(db: AsyncSession, session: Session) -> None:
        session.expires_at = datetime.now() + SessionRepository.SESSION_EXPIRE
        await db.commit()

    @staticmethod
    async def cleanup_expired(db: AsyncSession) -> None:
        await db.execute(delete(Session).where(Session.expires_at < datetime.now()))
        await db.commit()