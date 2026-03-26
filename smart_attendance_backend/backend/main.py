from fastapi.middleware.cors import CORSMiddleware

# ... after app = FastAPI() ...

# Add the specific URL of your frontend here
origins = [
    "https://smart-attendance-portal.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://smart-attendance-portal.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
