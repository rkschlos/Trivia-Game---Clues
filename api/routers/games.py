from datetime import datetime
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import psycopg
from .clues import ClueOut


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


class CustomGame(BaseModel):
    id: int
    created_on: datetime
    clues: list[ClueOut]
   
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

@router.post(
    "/api/custom-games",
    response_model = CustomGame
)
def create_custom_game():
    with psycopg.connect() as conn:
        with conn.cursor() as cur:
                # Uses the RETURNING clause to get the data
                # just inserted into the database. See
                # https://www.postgresql.org/docs/current/sql-insert.html
                cur.execute(
                    """
                    SELECT categories.id, categories.title, categories.canon,
                            clues.id, clues.answer, clues.question, clues.value,
                            clues.invalid_count, clues.canon
                    FROM categories
                        INNER JOIN clues
                        ON (clues.category_id = categories.id) 
                    WHERE clues.canon IS true
                    ORDER BY RANDOM() LIMIT 30
                """,
                )
                thirtyclues = cur.fetchall()
                with conn.transaction():
                # BEGIN is executed, a transaction started
                    cur.execute(
                        """
                        INSERT INTO game_definitions (created_on) 
                        VALUES (CURRENT_TIMESTAMP) RETURNING id, created_on
                        """
                    )
                    game_def = cur.fetchone()
                    game_def_id = game_def[0]
                    game_def_created_on = game_def[1]
                     # for each of the 30 clues from the first step
                    formatted_clues = []
                    for clue in thirtyclues:
                        clue_id = clue[0] 
                        cur.execute(
                        """
                        INSERT INTO game_definition_clues(game_definition_id, clue_id) 
                        VALUES (%s, %s)
                        """,
                        [game_def_id, clue_id],
                        )

                        pretty_clue = {
                            "id": clue[3],
                            "question": clue[4],
                            "answer": clue[5],
                            "value": clue[6],
                            "invalid_count": clue[7],
                            "canon": clue[8],
                            "category": {
                                "id": clue[0],
                                "title": clue[1],
                                "canon": clue[2]
                            }
                        }
                        formatted_clues.append(pretty_clue)
                        print("FORMATTED CLUES!", formatted_clues)

                    return {
                        "id": game_def_id,
                        "created_on": game_def_created_on, 
                        "clues": formatted_clues,
                    }

                            

                             #the id value for each one with the new id from the last step"
                         #into game_definiteion_clues
                #         """
                #         SELECT 
                #         """
                #     )
                    # These two operation run atomically in the same transaction

                    # COMMIT is executed at the end of the block.
                    # The connection is in idle state again.

                    #   The connection is closed at the end of the block.




            #     for clue in thirtyclues:

            # except psycopg.errors.UniqueViolation:
            #     # status values at https://github.com/encode/starlette/blob/master/starlette/status.py
            #     response.status_code = status.HTTP_409_CONFLICT
            #     return {
            #         "message": "Could not create duplicate category",
            #     }
            # row = cur.fetchone()
            # record = {}
            # for i, column in enumerate(cur.description):
            #     record[column.name] = row[i]
            # return record
