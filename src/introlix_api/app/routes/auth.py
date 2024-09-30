import random
from fastapi import APIRouter, HTTPException, Query

from introlix_api.exception import CustomException
from introlix_api.app.model import UserSignup, UserLogin
from introlix_api.app.appwrite import databases, APPWRITE_DATABASE_ID, ID, APPWRITE_ACCOUNT_COLLECTION_ID
from introlix_api.logger import logger

router = APIRouter()

@router.post('/signup')
async def signup(user: UserSignup):
    """
    Function to signup a new user
    """
    try:
        # List of avatar colors
        avatar_colors = [
            "#FF4500",  # Orange Red
            "#FF6347",  # Tomato
            "#FF7F50",  # Coral
            "#FF8C00",  # Dark Orange
            "#FFD700",  # Gold
            "#ADFF2F",  # Green Yellow
            "#32CD32",  # Lime Green
            "#00FA9A",  # Medium Spring Green
            "#40E0D0",  # Turquoise
            "#1E90FF",  # Dodger Blue
            "#4682B4",  # Steel Blue
            "#8A2BE2",  # Blue Violet
            "#FF69B4",  # Hot Pink
            "#FF1493",  # Deep Pink
            "#C71585"   # Medium Violet Red

            ]
        # Check if the email is already registered
        existing_users = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_ACCOUNT_COLLECTION_ID,
        )
        
        # Iterate through existing users to check if the email already exists
        for doc in existing_users['documents']:
            if doc['Email'] == user.email:
                raise HTTPException(status_code=400, detail="Email is already registered")
        
        # If email is not found, proceed with signup
        result = databases.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_ACCOUNT_COLLECTION_ID,
            document_id=ID.unique(),
            data={
                "Name": user.name,
                "Email": user.email,
                "Password": user.password,
                "DOB": user.dob.isoformat(),
                "interests": user.interestList,
                "profileColor": random.choice(avatar_colors)
            }
        )
        return {"message": "User created successfully", "document_id": result['$id']}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/login')
async def login(user: UserLogin):
    """
    Function to login a user
    """
    try:
        # List of users
        users = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_ACCOUNT_COLLECTION_ID
        )
        # Find user with matching email and password
        for doc in users['documents']:
            if doc['Email'] == user.email and doc['Password'] == user.password:
                return {"message": "Login successful", "document_id": doc['$id']}
        raise HTTPException(status_code=400, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/verify_it_user")
async def verify_user_exist(user_id: str = Query(...)):
    """
    Function to verify if the user exists
    """
    try:
        # List of users
        users = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=APPWRITE_ACCOUNT_COLLECTION_ID
        )

        # Find user with matching id
        for doc in users['documents']:
            if user_id == doc['$id']:
                return {"message": "It's User", "interests": doc["interests"], "name": doc["Name"][0], "profileColor": doc["profileColor"]}
        
        # If no matching user found
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))