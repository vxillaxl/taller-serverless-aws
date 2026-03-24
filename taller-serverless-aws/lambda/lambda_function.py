import boto3
import os
import urllib.parse
from io import BytesIO
from PIL import Image, ImageFilter, ImageDraw, ImageFont

s3 = boto3.client('s3')

# Variables de entorno configuradas en Lambda
BUCKET_DESTINO = os.environ.get('BUCKET_DESTINO', 'imagenes-destino-bryanramirez')


def lambda_handler(event, context):
    """
    Trigger: S3 Event - All object create events en el bucket de origen.
    Lee la imagen subida, aplica un filtro blur + marca de agua, y guarda
    el resultado en el bucket destino con prefijo 'procesada-'.
    """

    # 1. Obtener datos del evento S3
    record = event['Records'][0]
    bucket_origen = record['s3']['bucket']['name']
    key_origen = urllib.parse.unquote_plus(
        record['s3']['object']['key'], encoding='utf-8'
    )

    print(f"[INFO] Procesando: s3://{bucket_origen}/{key_origen}")

    # 2. Descargar imagen original desde S3
    response = s3.get_object(Bucket=bucket_origen, Key=key_origen)
    imagen_bytes = response['Body'].read()

    # 3. Abrir con Pillow
    imagen = Image.open(BytesIO(imagen_bytes)).convert('RGB')

    # 4a. Aplicar filtro BLUR (suavizado)
    imagen_procesada = imagen.filter(ImageFilter.GaussianBlur(radius=3))

    # 4b. Agregar marca de agua de texto
    draw = ImageDraw.Draw(imagen_procesada)
    ancho, alto = imagen_procesada.size

    texto = "Bryan Ramírez · AWS Lambda"
    # Tamaño de fuente proporcional al ancho de la imagen
    font_size = max(20, ancho // 25)

    try:
        # Intentar cargar fuente del sistema (disponible en Lambda con la layer correcta)
        font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationSans-Regular.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Posición: esquina inferior derecha con margen
    bbox = draw.textbbox((0, 0), texto, font=font)
    texto_ancho = bbox[2] - bbox[0]
    texto_alto = bbox[3] - bbox[1]
    margen = 20
    pos_x = ancho - texto_ancho - margen
    pos_y = alto - texto_alto - margen

    # Sombra + texto blanco semitransparente
    draw.text((pos_x + 2, pos_y + 2), texto, font=font, fill=(0, 0, 0, 128))
    draw.text((pos_x, pos_y), texto, font=font, fill=(255, 255, 255, 200))

    # 5. Guardar imagen procesada en memoria
    buffer = BytesIO()
    imagen_procesada.save(buffer, format='JPEG', quality=90)
    buffer.seek(0)

    # 6. Subir al bucket destino con prefijo 'procesada-'
    key_destino = f"procesada-{key_origen}"
    s3.put_object(
        Bucket=BUCKET_DESTINO,
        Key=key_destino,
        Body=buffer.getvalue(),
        ContentType='image/jpeg'
    )

    print(f"[OK] Guardado en: s3://{BUCKET_DESTINO}/{key_destino}")

    return {
        'statusCode': 200,
        'body': f'Imagen procesada y guardada en {BUCKET_DESTINO}/{key_destino}'
    }
