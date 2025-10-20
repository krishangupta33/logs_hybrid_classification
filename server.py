from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI(title="Log Classification API", version="1.0.0")


@app.get("/")
async def root():
    """Health check endpoint to verify server is running"""
    return JSONResponse(
        content={
            "status": "online",
            "message": "Log Classification API is running",
            "endpoints": {
                "health": "/",
                "classify": "/classify/ (POST)"
            }
        }
    )


@app.get("/health")
async def health_check():
    """Alternative health check endpoint"""
    return {"status": "healthy"}


@app.post("/classify/")
async def classify_logs(file: UploadFile):
    # Lazy import to avoid startup errors
    import pandas as pd
    from classify import classify
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV.")
    
    try:
        # Read the uploaded CSV
        df = pd.read_csv(file.file)
        
        if "source" not in df.columns or "log_message" not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="CSV must contain 'source' and 'log_message' columns."
            )

        # Perform classification
        df["target_label"] = classify(list(zip(df["source"], df["log_message"])))

        print("Dataframe:", df.to_dict())

        # Ensure resources directory exists
        os.makedirs("resources", exist_ok=True)
        
        # Save the modified file
        output_file = "resources/output.csv"
        df.to_csv(output_file, index=False)
        print(f"File saved to {output_file}")
        
        return FileResponse(
            output_file, 
            media_type='text/csv',
            filename='classified_logs.csv'
        )
        
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
