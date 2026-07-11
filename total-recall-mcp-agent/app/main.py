# def main():
#     print("Hello from total-recall-mcp!")


# if __name__ == "__main__":
#     main()

from fastapi import FastAPI

# from app.database import engine

app = FastAPI()

"""
Returns a dummy message that MCP server is running
"""


@app.get("/")
def home():
    """Returns a dummy message that MCP server is running"""
    return {"message": "Hello from total-recall-mcp!"}
