from fastapi import FastAPI, Path, Query, Request,HTTPException,Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from utils.jwt_manager import create_token, decode_token
from fastapi.security import HTTPBearer
from config.database import Session, engine, Base
from models.movie import Movie as MovieModel 
from fastapi.encoders import jsonable_encoder

app = FastAPI()
app.title = "Movies API"
app.version = "0.0.1"

Base.metadata.create_all(bind = engine)

class JWTBearer(HTTPBearer):
    async def __call__(self,request: Request):
        auth = await super().__call__(request)
        data = decode_token(auth.credentials)
        if data['email'] != "admin@gmail.com":
            raise HTTPException(status_code=403, detail = "Credenciales inválidas")

class User(BaseModel):
    email:str
    password:str

class Movie(BaseModel):
    id: Optional[int] = None
    title: str = Field(max_length=100, min_length=1, default="Título de la película")
    overview: str = Field(max_length=500, min_length=10, default="Resumen de la película")
    year: int = Field(ge=1900, le=2100, default=2000)
    category: str = Field(max_length=50, min_length=3, default="Categoría de la película")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Inception",
                "overview": "Un ladrón especializado en el robo de secretos corporativos a través del sueño es contratado para implantar una idea en la mente de un ejecutivo.",
                "year": 2010,
                "category": "Ciencia ficción"
            }
        }

@app.get("/", tags=["home"])
def message():
    return {"message": "Hello World"}

@app.get("/movies", tags=["Movies"], dependencies=[Depends(JWTBearer())])
def get_movies():
    db = Session()
    result = db.query(MovieModel).all()
    return JSONResponse(content=jsonable_encoder(result), status_code=200)

@app.get("/movies/{id}", tags=["Movies"], dependencies=[Depends(JWTBearer())])
def get_movie(id: int = Path(ge=1, le=2100)):
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first()
    if not result:
        return JSONResponse(status_code=404, content={"message": "Película no encontrada"})
    return JSONResponse(status_code=200, content=jsonable_encoder(result))


@app.get("/movies/", tags=["Movies"], dependencies=[Depends(JWTBearer())])
def get_movie_by_category(category: str = Query(min_length=3, max_length=50)):
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.category == category).all()
    if not result:
        return JSONResponse(status_code=404, content={"message": "Películas no encontradas"})
    return JSONResponse(status_code=200, content=jsonable_encoder(result))


@app.post("/movies", tags=["Movies"], dependencies=[Depends(JWTBearer())])
def create_movie(movie: Movie):
    db = Session()
    new_movie = MovieModel(**movie.model_dump())
    db.add(new_movie)
    db.commit()
    return JSONResponse(content=jsonable_encoder(new_movie), status_code=201)


@app.patch("/movies/{id}", tags=["Movies"],dependencies=[Depends(JWTBearer())])
def update_movie(id: int, movie: Movie):
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first()
    if not result: 
        return JSONResponse(status_code=404, content={"message": "Película no encontrada"})
    
    result.title = movie.title
    result.overview = movie.overview
    result.year = movie.year
    result.category = movie.category
    db.commit()
    
    return JSONResponse(content={"message": "Actualizado correctamente", "movie": jsonable_encoder(result)}, status_code=200)


@app.delete("/movies/{id}", tags=["Movies"], dependencies=[Depends(JWTBearer())])
def delete_movie(id: int):
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first()
    if not result:
        return JSONResponse(status_code=404, content={"message": "Película no encontrada"})
    
    db.delete(result)
    db.commit()

    return JSONResponse(content={"message": "Película eliminada correctamente", "movie": jsonable_encoder(result)}, status_code=200)


@app.post('/login',tags=['auth'])
def login(user:User):
    if user.email == "admin@gmail.com" and user.password == "admin":
        token:str = create_token(user.dict())
        return JSONResponse(status_code=200, content=token)
