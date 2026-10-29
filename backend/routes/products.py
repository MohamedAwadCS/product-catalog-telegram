from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException, Response

from storage import save_product

router = APIRouter()

@router.post("/products")
def create_product(request: Request, name: str = Form(), image_unique_id: str = Form(), photo: UploadFile = File()):
    # Checking and validating inputs
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is needed")

    if not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")

    save_product(name, image_unique_id, photo.file, photo.size)
    return {"status": "done"}


@router.get("/products")
def get_products(request: Request):
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, created_at FROM products ORDER BY id DESC")
            products = cursor.fetchall()
            return {"products": [{"id": p[0], "name": p[1], "created_at": p[2]} for p in products]}


@router.get("/products/{id}/photo")
def get_product_photo(request: Request, id: int):
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT minio_image_key FROM products WHERE id = %s", (id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404)

    bucket = request.app.state.bucket
    key = result[0]
    data = request.app.state.minio.get_object(bucket, key).read()
    return Response(content=data, media_type="image/jpeg")