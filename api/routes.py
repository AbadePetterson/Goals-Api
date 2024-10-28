from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import Token
from schemas.user import UserCreate, User
from services.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user,
    get_current_user
)
from schemas.goal import Goal, GoalCreate, GoalUpdate, GoalStatus
from schemas.step import Step, StepCreate, StepUpdate
from models.goal import GoalDB
from models.step import StepDB
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=User)
async def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    return create_user(db=db, user=user)

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):

    return current_user


@router.get("/users/{username}", response_model=User)
async def read_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = get_user(db, username=username)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.post("/goals/", response_model=Goal)
async def create_goal(
    goal: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_goal = GoalDB(**goal.dict(), user_id=current_user.id)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.get("/goals/", response_model=List[Goal])
async def get_goals(
    status: Optional[GoalStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(GoalDB).filter(GoalDB.user_id == current_user.id)
    if status:
        query = query.filter(GoalDB.status == status)
    return query.all()

@router.get("/goals/{goal_id}", response_model=Goal)
async def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goal = db.query(GoalDB).filter(
        GoalDB.id == goal_id,
        GoalDB.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal

@router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: int,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_goal = db.query(GoalDB).filter(
        GoalDB.id == goal_id,
        GoalDB.user_id == current_user.id
    ).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    for key, value in goal_update.dict(exclude_unset=True).items():
        setattr(db_goal, key, value)
    
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_goal = db.query(GoalDB).filter(
        GoalDB.id == goal_id,
        GoalDB.user_id == current_user.id
    ).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(db_goal)
    db.commit()
    return {"message": "Goal deleted"}

# Rotas de Steps
@router.post("/goals/{goal_id}/steps/", response_model=Step)
async def create_step(
    goal_id: int,
    step: StepCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goal = db.query(GoalDB).filter(
        GoalDB.id == goal_id,
        GoalDB.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db_step = StepDB(**step.dict(), goal_id=goal_id)
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    
    update_goal_progress(db, goal)
    return db_step

@router.put("/goals/{goal_id}/steps/{step_id}", response_model=Step)
async def update_step(
    goal_id: int,
    step_id: int,
    step_update: StepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goal = db.query(GoalDB).filter(
        GoalDB.id == goal_id,
        GoalDB.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db_step = db.query(StepDB).filter(
        StepDB.id == step_id,
        StepDB.goal_id == goal_id
    ).first()
    if not db_step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    for key, value in step_update.dict(exclude_unset=True).items():
        setattr(db_step, key, value)
    
    if step_update.is_completed:
        db_step.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_step)
    
    update_goal_progress(db, goal)
    return db_step

# Função auxiliar para atualizar o progresso da meta
def update_goal_progress(db: Session, goal: GoalDB):
    total_steps = len(goal.steps)
    if total_steps > 0:
        completed_steps = len([s for s in goal.steps if s.is_completed])
        goal.progress = int((completed_steps / total_steps) * 100)
        if goal.progress == 100:
            goal.status = GoalStatus.COMPLETED
        db.commit()