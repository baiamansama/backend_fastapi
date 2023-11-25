# boards/board_api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_users import fastapi_users, FastAPIUsers
from sqlalchemy import func
from auth.database import User
from auth.manager import get_user_manager
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from auth.schemas import UserRead
from models.models import board, user, post
from auth.auth import auth_backend
from auth.database import get_async_session

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()


@router.post("/create_post")
async def create_post(
    board_id: int,
    title: str,
    content: str,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_board = await session.execute(select(board).where(board.c.id == board_id))
    existing_board_record = existing_board.scalar()
    print(existing_board_record)

    if not existing_board_record:
        raise HTTPException(status_code=404, detail="Board not found")
    creator_id = (await session.execute(select(board.c.creator_id).where(board.c.id == board_id))).scalar_one()
    public = (await session.execute(select(board.c.public).where(board.c.id == board_id))).scalar_one()
    if not public and creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You cannot create a post on this board")

    existing_post = await session.execute(select(post).where((post.c.board_id == board_id) & (post.c.title == title)))
    if existing_post.scalar():
        raise HTTPException(status_code=400, detail="Post with this title already exists on the board")

    new_post_values = {"title": title, "content": content, "creator_id": current_user.id, "board_id": board_id}
    await session.execute(insert(post).values(new_post_values))
    await session.commit()

    return {"message": "Post created successfully"}

@router.put("/update_post/{post_id}")
async def update_post(
    post_id: int,
    title: str,
    content: str,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_post = await session.execute(select(post).where(post.c.id == post_id))
    post_record = existing_post.scalar()

    if not post_record:
        raise HTTPException(status_code=404, detail="Post not found")

    creator_id = (await session.execute(select(post.c.creator_id).where(post.c.id == post_id))).scalar_one()
    if creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You are not the creator of this post")

    updated_post_values = {"title": title, "content": content}
    await session.execute(update(post).where(post.c.id == post_id).values(updated_post_values))
    await session.commit()

    return {"message": "Post updated successfully"}

@router.delete("/delete_post/{post_id}")
async def delete_post(
    post_id: int,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_post = await session.execute(select(post).where(post.c.id == post_id))
    post_record = existing_post.scalar()

    if not post_record:
        raise HTTPException(status_code=404, detail="Post not found")
    creator_id = (await session.execute(select(post.c.creator_id).where(post.c.id == post_id))).scalar_one()
    if creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You are not the creator of this post")

    await session.execute(delete(post).where(post.c.id == post_id))
    await session.commit()

    return {"message": "Post deleted successfully"}

@router.get("/get_post/{post_id}")
async def get_post(
    post_id: int,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_post = await session.execute(select(post).where(post.c.id == post_id))
    post_record = existing_post.scalar()

    if not post_record:
        raise HTTPException(status_code=404, detail="Post not found")
    creator_id = (await session.execute(select(post.c.creator_id).where(post.c.id == post_id))).scalar_one()
    public = (await session.execute(select(board.c.public).where(board.c.id == post_record.board_id))).scalar_one()

    if not public and creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You cannot view this post")
    post_record = existing_post.all()
    # print(post_record)
    post_info = {
        "id": post_record.id,
        "title": post_record.title,
        "content": post_record.content,
        "creator_id": post_record.creator_id,
        "board_id": post_record.board_id,
        "created_at": post_record.created_at,
    }

    return {"message": "Post details retrieved successfully", "post_info": post_info}

@router.get("/list_posts/{board_id}")
async def list_posts(
    board_id: int,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = select(post).where((post.c.board_id == board_id) & ((board.c.public == True) | (board.c.creator_id == current_user.id)))
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    post_records = result.all()
    formatted_posts = [
        {
            "id": post_record[0],
            "title": post_record[1],
            "content": post_record[2],
            "creator_id": post_record[3],
            "board_id": post_record[4],
            "created_at": post_record[5],
        }
        for post_record in post_records
    ]

    return formatted_posts
