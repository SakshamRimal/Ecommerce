from app.api.v1.auth.repository import UserRepository
from app.api.v1.auth.schema import UserRegisterRequest , TokenResponse , UserResponse
from app.core.security import decode_token, hash_password , create_access_token , create_refresh_token , verify_password
from app.core.exceptions import ConflictError , UnauthorizedError

class AuthService:
    
    def __init__(self , repository:UserRepository):
        self.repository = repository
        
    async def register(self , data:UserRegisterRequest) -> UserResponse:
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise ConflictError("Email already exists")
        
        hash = hash_password(data.password)
        user = await self.repository.create(data.email , hash , data.full_name)
        
        return UserResponse.model_validate(user)
    
    async def login(self , email: str , password: str) -> TokenResponse:
        
        user = await self.repository.get_by_email(email)
        if not user or not verify_password(password , user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("User is inactive")
        
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return TokenResponse(access_token=access_token , refresh_token=refresh_token)
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        # Here you would typically verify the refresh token and extract the user ID
        
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        
        user_id = payload["sub"]
        access_token = create_access_token(subject=user_id)
        new_refresh_token = create_refresh_token(subject=user_id)
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
            
        
        
        