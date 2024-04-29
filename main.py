import asyncio
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi_pagination import Page
from fastapi_pagination.paginator import paginate
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tokenize import Token
from typing import List
from models.user import Base, create_user, Role, Category, todo_categories,Todos
from fastapi import APIRouter
from config.db import conn,SessionLocal
from schemas.user import TodoCreate, Todo, TodoUpdate, UserCreate, User, PaginateParams, SearchUser, Login
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
import uvicorn


SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password hashing
def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password:str):
    return pwd_context.hash(password)

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI app
app = FastAPI()
router=APIRouter()
security = HTTPBasic()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authorization function
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Authentication
    if token != "validtoken":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return User


# Routes for managing todos (authorization required)

@app.post("todos", tags=["Admin Use"])
def get_todos(request:User,role: int, db: Session = Depends(get_db)):
    user = db.query(create_user).filter(create_user.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username or password",)
    
    if not verify(request.password, user.password):
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Invalid Password",
         )

    if role != 1:
        return {"message": "User can not access users"}
    todos=db.query(Todos).all()
    return todos

#Get all users
@app.post("/user/", tags=["Admin Use"])
def get_users(request:User,role: int, db: Session = Depends(get_db)):
    user = db.query(create_user).filter(create_user.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username or password",)
    
    if not verify(request.password, user.password):
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Invalid Password",
         )

    if role != 1:
        return {"message": "User can not access users"}
    
    users = db.query(create_user).all()
    return users
  

# Pagination and filtering example
@app.post("/todos/paginated/",response_model=List[PaginateParams], tags=["Admin Use"])
def get_paginated_todos(request:User,role: int,skip: int = 0, limit: int = 10,db: Session = Depends(get_db)):
    user=db.query(create_user).filter(create_user.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username or password",)
    
    if not verify(request.password, user.password):
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Invalid Password",
         )

    if role != 1:
        return {"message": "User can not access users"}
    
    return list(Todos())[skip : skip + limit]

# AsyncIO
def process_todo(todo_id: int):
    #asyncIO function
    todo = Todos.get(todo_id)
    if todo:
        todo.status = "completed"

@app.post("/todos/{todo_id}/complete",response_model=UserCreate, tags=["Admin Use"])
async def complete_todo(request:User,role: int, todo_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user=db.query(create_user).filter(create_user.username == request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid username or password",)
    
    if not verify(request.password, user.password):
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail="Invalid Password",
         )

    if role != 1:
        return {"message": "User can not access users"}
    
    return {"message": "Todo completion scheduled"}


# Endpoint for user registration
@app.post("/register/Role 1: admin, Role 2 regular ",response_model=UserCreate, tags=["Authentication"])
def register_user(username: str,role: int, password: str, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(password)
    user = create_user(username=username,role_id=role, password=hashed_password)
    
    if role > 2:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Invalid role id"
        )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
    


# Endpoint for creating a new todo
@app.post("/todos/", response_model=TodoCreate,tags=["Todoes"])
def create_todo(todo_data: TodoCreate, db: Session = Depends(get_db)):
    todo_dict=todo_data.dict()
    todo = Todos(**todo_dict)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return {"messege":"Todo created successfully","todo":todo}

# Endpoint for updating a todo
@app.put("/todos/{todo_id}", response_model=TodoCreate,tags=["Todoes"])
def update_todo(todo_id: int, todo_data: dict, db: Session = Depends(get_db)):
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    for key, value in todo_data.items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return {"messege":"Todo updated successfully","todo":todo}
 

# Endpoint for deleting a todo
@app.delete("/todos/{todo_id}",tags=["Todoes"])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}


# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
