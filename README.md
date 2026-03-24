# Taller Cloud Computing — Arquitectura Serverless en AWS
### Procesamiento automatico de imagenes con S3 + Lambda + Pillow

**Autor:** Bryan Ramirez  
**Materia:** Electiva II  
**Tecnologias:** AWS S3 · AWS Lambda · Python · Pillow · AWS SDK for JavaScript

---

## Arquitectura

```
+------------------------------------------------------------------+
|                        NAVEGADOR (usuario)                       |
|                         index.html + AWS SDK JS                  |
+---------------+-------------------------+------------------------+
                | 1. PUT objeto           | 5. GET objeto firmado
                v                         v
+----------------------+       +----------------------+
|  S3 - Bucket ORIGEN  |       |  S3 - Bucket DESTINO |
| imagenes-origen-...  |       | imagenes-destino-... |
+-----------+----------+       +----------------------+
            | 2. Evento S3                  ^
            |    (All object create)        | 4. PUT objeto procesado
            v                               |
+------------------------------------------------------+
|                   AWS Lambda                         |
|            procesador-imagenes (Python 3.12)         |
|                                                      |
|  3. Lee imagen -> aplica GaussianBlur + marca de agua|
|     -> guarda con prefijo "procesada-"               |
+------------------------------------------------------+
            |
            v
+----------------------+
|   IAM Role           |
|  S3:GetObject (origen|
|  S3:PutObject (dest) |
|  CloudWatch Logs     |
+----------------------+
```

### Flujo completo paso a paso

1. El usuario abre `index.html`, ingresa sus credenciales AWS y selecciona una imagen
2. El SDK de AWS sube la imagen al **bucket de origen** (`imagenes-origen-bryanramirez`)
3. S3 dispara automaticamente el **trigger** sobre la funcion Lambda
4. Lambda descarga la imagen, aplica un **filtro GaussianBlur** y una **marca de agua** con Pillow, y guarda el resultado en el **bucket de destino** con prefijo `procesada-`
5. El frontend hace **polling cada 3 segundos** (hasta 60s) usando `headObject` hasta confirmar que la imagen procesada ya existe
6. Se genera una **URL firmada** (presigned URL) y se muestra la imagen con opcion de descarga

---

## Estructura del repositorio

```
taller-serverless-aws/
├── README.md
├── frontend/
│   └── index.html          # Interfaz web - sube imagen y muestra resultado
└── lambda/
    └── lambda_function.py  # Codigo de la funcion Lambda (Python + Pillow)
```

---

## Configuracion AWS

### Fase 1 — Buckets S3

| Bucket | Proposito | Acceso |
|--------|-----------|--------|
| `imagenes-origen-bryanramirez` | Recibe imagenes del usuario | PUT publico (CORS) |
| `imagenes-destino-bryanramirez` | Almacena imagenes procesadas | GET publico (CORS) |

**CORS aplicado en ambos buckets:**
```json
[{
  "AllowedHeaders": ["*"],
  "AllowedMethods": ["PUT", "POST", "GET", "HEAD"],
  "AllowedOrigins": ["*"],
  "ExposeHeaders": ["ETag"]
}]
```

### Fase 2 — Funcion Lambda

| Parametro | Valor |
|-----------|-------|
| Runtime | Python 3.12 |
| Timeout | 30 segundos |
| Layer | Pillow (Klayers) |
| Trigger | S3 -> All object create events (bucket origen) |
| Variable de entorno | `BUCKET_DESTINO = imagenes-destino-bryanramirez` |

**Rol IAM (`lambda-procesador-imagenes-role`):**
- `s3:GetObject` sobre bucket origen
- `s3:PutObject` sobre bucket destino
- `AWSLambdaBasicExecutionRole` (logs en CloudWatch)

### Fase 3 — Integracion frontend

El frontend implementa polling activo para detectar cuando Lambda termina:

```javascript
for (let intento = 1; intento <= 20; intento++) {
  await new Promise(r => setTimeout(r, 3000)); // espera 3s
  try {
    await s3.headObject({ Bucket: BUCKET_DESTINO, Key: key_procesada }).promise();
    // imagen lista
    break;
  } catch (e) {
    // aun no esta, continuar esperando
  }
}
```

Una vez confirmada la existencia, genera una presigned URL valida por 10 minutos y la muestra con opcion de descarga.

---

## Como usar

1. Clonar este repositorio
2. Abrir `frontend/index.html` en el navegador (o desplegarlo en el bucket de hosting S3)
3. Ingresar las credenciales AWS:
   - Access Key ID
   - Secret Access Key
   - Session Token (solo si se usa AWS Academy / Learner Lab)
4. Seleccionar o arrastrar una imagen (JPG, PNG, WEBP)
5. Hacer clic en "Subir imagen al bucket de origen"
6. Esperar mientras Lambda procesa — el progreso se muestra en tiempo real
7. Descargar la imagen procesada con el filtro blur y la marca de agua aplicados

Nota: en AWS Academy las credenciales expiran cada 4 horas. Copiar siempre el Session Token completo desde el panel de Learner Lab.

---

## Tecnologias utilizadas

- **AWS S3** — Almacenamiento de objetos y hosting estatico
- **AWS Lambda** — Computo serverless activado por eventos
- **AWS IAM** — Gestion de roles y politicas de seguridad
- **Python 3.12 + Pillow** — Procesamiento de imagenes en Lambda
- **AWS SDK for JavaScript v2** — Interaccion con S3 desde el navegador
- **HTML5 / CSS3 / JavaScript** — Interfaz de usuario
