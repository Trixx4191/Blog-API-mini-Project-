from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import warnings
warnings.simplefilter("ignore", category=UserWarning)
# App & Database Configuration


# Initialize the FastAPI app
app = FastAPI()

# SQLite database URL
DATABASE_URL = "sqlite:///./blog.db"

# Set up the SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models


# SQLAlchemy model: Defines what a Post looks like in the DB
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the posts table if it doesn't already exist
Base.metadata.create_all(bind=engine)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas


# What the client is allowed to send (input model)
class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True

# What we return back to the client (output model)
class PostOut(PostCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Routes


@app.get("/")
def greet():
    # Simple welcome message
    return {"message": "Welcome to The Path!"}

@app.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    # Create a new post in the database
    new_post = Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.get("/posts", response_model=List[PostOut])
def get_posts(db: Session = Depends(get_db)):
    # Get all posts
    posts = db.query(Post).all()
    return posts

@app.get("/posts/{id}", response_model=PostOut)
def get_single_post(id: int, db: Session = Depends(get_db)):
    # Get a specific post by ID
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{id}", response_model=PostOut)
def update_post(id: int, updated_post: PostCreate, db: Session = Depends(get_db)):
    # Update an existing post
    post_query = db.query(Post).filter(Post.id == id)
    post = post_query.first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()

@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    # Delete a post by ID
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return