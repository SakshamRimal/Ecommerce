from pydantic import BaseModel , Field 

class ChatRequest(BaseModel):
    message: str = Field(min_length=1 , max_length=1000 , description="The user's message to the chat assistant.")
    
class ChatResponse(BaseModel):
    reply: str = Field(description="The assistant's reply to the user's message.")