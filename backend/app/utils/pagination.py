"""
Cursor 分页工具
支持基于 keyset 的高效分页
"""

import base64
import json
from typing import Generic, TypeVar, Optional, Type
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar("T")


def encode_cursor(item: dict, order_by: str) -> str:
    """
    编码游标。
    
    Args:
        item: 数据行字典
        order_by: 排序字段名
        
    Returns:
        Base64 编码的游标字符串
    """
    # 简化：直接用 id 字段
    cursor_data = {
        "id": item.get("id") or item.get("id"),
    }
    return base64.urlsafe_b64encode(json.dumps(cursor_data).encode()).decode()


def decode_cursor(cursor: str) -> Optional[dict]:
    """
    解码游标。
    
    Args:
        cursor: Base64 编码的游标字符串
        
    Returns:
        游标数据字典，解析失败返回 None
    """
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return data
    except Exception:
        return None


class CursorPaginator(Generic[T]):
    """
    Cursor 分页器。
    
    使用示例:
        paginator = CursorPaginator(db, Job, order_by="created_at", limit=20)
        result = await paginator.paginate(after=cursor)
    """

    def __init__(
        self,
        db: AsyncSession,
        model: Type[T],
        order_by: str = "created_at",
        limit: int = 20,
        desc: bool = True,
    ):
        self.db = db
        self.model = model
        self.order_by = order_by
        self.limit = limit
        self.desc = desc

    async def paginate(
        self,
        after: Optional[str] = None,
        before: Optional[str] = None,
        filters: Optional[dict] = None,
    ) -> dict:
        """
        执行分页查询。
        
        Args:
            after: 返回 cursor 之后的数据（下一页）
            before: 返回 cursor 之前的数据（上一页）
            filters: 额外过滤条件
            
        Returns:
            {
                "items": [...],
                "next_cursor": str | None,
                "prev_cursor": str | None,
                "has_more": bool
            }
        """
        # 构建基础查询
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        # 应用过滤
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
                    count_query = count_query.where(getattr(self.model, key) == value)

        # 应用游标
        if after:
            cursor_data = decode_cursor(after)
            if cursor_data and "id" in cursor_data:
                order_col = getattr(self.model, self.order_by)
                if self.desc:
                    query = query.where(order_col < cursor_data.get(self.order_by))
                else:
                    query = query.where(order_col > cursor_data.get(self.order_by))

        # 排序
        order_col = getattr(self.model, self.order_by)
        if self.desc:
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # 查询 limit + 1 条判断是否有更多
        query = query.limit(self.limit + 1)

        # 执行查询
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        # 判断是否有更多
        has_more = len(items) > self.limit
        if has_more:
            items = items[:-1]

        # 构建响应
        response = {
            "items": [self._model_to_dict(item) for item in items],
            "has_more": has_more,
            "next_cursor": None,
            "prev_cursor": None,
        }

        # 生成游标
        if items:
            first_item = self._model_to_dict(items[0])
            last_item = self._model_to_dict(items[-1])

            if has_more:
                response["next_cursor"] = encode_cursor(last_item, self.order_by)
            response["prev_cursor"] = encode_cursor(first_item, self.order_by)

        return response

    def _model_to_dict(self, item: T) -> dict:
        """将模型实例转为字典"""
        if isinstance(item, dict):
            return item
        result = {}
        for col in item.__table__.columns:
            value = getattr(item, col.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[col.name] = value
        return result
