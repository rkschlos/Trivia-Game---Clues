from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import psycopg
from .categories import CategoryOut

router = APIRouter()

class ClueIn(BaseModel):
    answer: str
    question: str

class ClueOut(BaseModel):
    id: int
    question: str
    answer: str
    value: int
    invalid_count: int
    canon: bool
    category: CategoryOut

class Clues(BaseModel):
    page_count: int
    clues: list[ClueOut]

class Message(BaseModel):
    message:str

# get list

@router.get("/api/clues/{page}", response_model = Clues)
def clues_list(page: int = 0):
    with psycopg.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT categories.id, categories.title, categories.canon,
                        clues.id, clues.question, clues.answer,
                        clues.value, clues.invalid_count, 
                        clues.canon
                FROM categories
                    INNER JOIN clues
                    ON (clues.category_id = categories.id)
                ORDER BY clues.id
                LIMIT 100 OFFSET %s
            """, 
                [page * 100],
            )
            results = []
            for row in cur.fetchall():
                record = {
                    "id": row[3],
                    "question": row[4],
                    "answer": row[5],
                    "value": row[6],
                    "invalid_count": row[7],
                    "canon": row[8],
                    "category": {
                        "id": row[0],
                        "title": row[1],
                        "canon": row[2],
                    }
                }
                results.append(record)

            cur.execute(
                """
                SELECT COUNT(*) FROM clues;
            """
            )
            raw_count = cur.fetchone()[0]
            page_count = (raw_count // 100) + 1

            return Clues(page_count=page_count, clues=results)

#get detail

# @router.get(
#     "/api/random-clue/{clue_id}",
#     response_model=ClueOut,
#     responses={404: {"model": Message}},
# )
# def get_clue(clue_id: int, response: Response):
#     with psycopg.connect("postgresql://trivia-game:trivia-game@db/trivia-game") as conn:
#         with conn.cursor() as cur:
#             cur.execute(
#                 f"""
#                 SELECT clues.id, clues.answer, clues.question,
#                         clues.value, clues.invalid_count, 
#                         categories.id, categories.title, categories.canon,
#                         clues.canon
#                 FROM categories
#                     INNER JOIN clues
#                     ON (clues.category_id = categories.id)
#                 WHERE clues.id = %s
#             """,
#                 [clue_id],
#             )
#             row = cur.fetchone()
#             print("row is", row)
#             if row is None:
#                 response.status_code = status.HTTP_404_NOT_FOUND
#                 return {"message": "Category not found"}
#             record = {}
#             for i, column in enumerate(cur.description):
#                 record[column.name] = row[i]
#             return record


            # row = cur.fetchone()
            # return {
            #     "id": row[3],
            # }