# boards/board_api.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import fastapi_users, FastAPIUsers
from sqlalchemy import desc, func
from auth.database import User
from auth.manager import get_user_manager
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from auth.schemas import UserRead
from models.models import board, user, post
from auth.auth import auth_backend
from auth.database import get_async_session

router = APIRouter(
    prefix="/boards",
    tags=["Boards"]
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
@router.post("/create_board")
async def create_board(
    name: str,
    public: bool,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_board = await session.execute(select(board).where(board.name== name))
    if existing_board.scalar():
        raise HTTPException(status_code=400, detail="Board with this name already exists")
    new_board_values = {"name": name, "public": public, "creator_id": current_user.id}
    await session.execute(insert(board).values(new_board_values))
    await session.commit()
    return {"message": "Board created successfully"}


@router.put("/update_board/{board_id}")
async def update_board(
    board_id: int,
    name: str,
    public: bool,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_board = await session.execute(select(board).where(board.c.id == board_id))
    board_record = existing_board.scalar()

    if not board_record:
        raise HTTPException(status_code=404, detail="Board not found")
    
    creator_id = (await session.execute(select(board.c.creator_id).where(board.c.id == board_id))).scalar_one()
    if creator_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You are not the creator of this board")
    
    updated_board_values = {"name": name, "public": public}
    await session.execute(update(board).where(board.c.id == board_id).values(updated_board_values))
    await session.commit()
    return {"message": "Board updated successfully"}


@router.delete("/delete_board/{board_id}")
async def delete_board(
    board_id: int,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    existing_board = await session.execute(select(board).where(board.c.id == board_id))
    board_record = existing_board.scalar()

    if not board_record:
        raise HTTPException(status_code=404, detail="Board not found")

    creator_id = (await session.execute(select(board.c.creator_id).where(board.c.id == board_id))).scalar_one()
    if creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied. You are not the creator of this board")

    await session.execute(delete(board).where(board.c.id == board_id))
    await session.commit()

    return {"message": "Board deleted successfully"}


@router.get("/get_board/{board_id}")
async def get_board(
    board_id: int,
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(board).where((board.c.id == board_id) & ((board.c.public == True) | (board.c.creator_id == current_user.id)))
    existing_board = await session.execute(query)
    board_record = existing_board.scalar()
    if not board_record:
        raise HTTPException(status_code=404, detail="Board not found")
    existing_board = await session.execute(query)
    nboard = existing_board.all()
    # print(nboard)
    formatted_board = [{
        "id": b[0],
        "name": b[1],
        "public": b[2],
        "creator_id": b[3],
        "created_at": b[4],
    }
    for b in nboard
    ]
    return formatted_board


@router.get("/list_boards")
async def list_boards(
    current_user: UserRead = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(board, func.count(post.c.id).label("post_count")).\
        outerjoin(post, board.c.id == post.c.board_id).\
        group_by(board.c.id)

    if current_user.is_active:
        query = query.where((board.c.public == True) | (board.c.creator_id == current_user.id))
    else:
        query = query.where(board.c.public == True)
    query = query.order_by(desc("post_count"))
    result = await session.execute(query)
    board_records = result.all()

    # print(board_records)
    #[(2, 'test-new', True, 1, datetime.datetime(2023, 11, 21, 2, 45, 1, 765392), 1), (3, 'test-new-2', False, 1, datetime.datetime(2023, 11, 21, 2, 46, 53, 14324), 0)]
    formatted_boards = [
        {
            "id": board[0],
            "name": board[1],
            "public": board[2],
            "creator_id": board[3],
            "created_at": board[4],
            "post_count": board[5],
        }
        for board in board_records
    ]

    return formatted_boards