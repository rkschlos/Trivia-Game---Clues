import string
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import psycopg

router = APIRouter()

class GameIn(BaseModel):
    title: str

class GameOut(BaseModel):
    id: int
    episode_id: int
    aired: str
    canon: bool

class GameWithTotalWon(GameOut):
    total_amount_won: int

class Games(BaseModel):
    page_count: int
    games: GameWithTotalWon

class Message(BaseModel):
    message:str

@router.get(
    "/api/game/{game_id}",
    response_model=GameWithTotalWon,
    responses={404: {"model": Message}},
)
def get_game(game_id: int, response: Response):
    with psycopg.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT games.id, games.episode_id, games.aired, games.canon, 
                SUM(clues.value) AS total_amount_won
                FROM games
                    LEFT OUTER JOIN clues
                    ON (clues.game_id = games.id)
                WHERE games.id = %s
                GROUP BY games.id, games.episode_id, games.aired, games.canon
            """,
                [game_id],
            )
            row = cur.fetchone()
            if row is None:
                response.status_code = status.HTTP_404_NOT_FOUND
                return {"message": "Category not found"}
            record = {
                "id": row[0],
                "episode_id": row[1],
                "aired": row[2],
                "canon": row[3],
                "total_amount_won": row[4] 
                }
            return record

