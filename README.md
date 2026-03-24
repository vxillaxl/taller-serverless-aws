# ☁️ Taller Cloud Computing — Arquitectura Serverless en AWS
### Procesamiento automático de imágenes con S3 + Lambda + Pillow

**Autor:** Bryan Ramírez  
**Materia:** Cloud Computing  
**Tecnologías:** AWS S3 · AWS Lambda · Python · Pillow · AWS SDK for JavaScript

---

## 📐 Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        NAVEGADOR (usuario)                      │
│                         index.html + AWS SDK JS                 │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ 1. PUT objeto            │ 5. GET objeto firmado
               ▼                          ▼
┌──────────────────────┐      ┌──────────────────────┐
│  S3 — Bucket ORIGEN  │      │  S3 — Bucket DESTINO │
│ imagenes-origen-...  │      │ imagenes-destino-... │
└──────────┬───────────┘      └──────────────────────┘
           │ 2. Evento S3                 ▲
           │    (All object create)       │ 4. PUT objeto procesado
           ▼                              │
┌──────────────────────────────────────────────────────┐
│                   AWS Lambda                         │
│            procesador-imagenes (Python 3.12)         │
│                                                      │
│  3. Lee imagen → aplica GaussianBlur + marca de agua │
│     → guarda con prefijo "procesada-"                │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   IAM Role           │
│  S3:GetObject (origen│
│  S3:PutObject (dest) │
│  CloudWatch Logs     │
└──────────────────────┘
```

### Flujo completo paso a paso

1. El usuario abre `index.html`, ingresa sus credenciales AWS y selecciona una imagen
2. El SDK de AWS sube la imagen al **bucket de origen** (`imagenes-origen-bryanramirez`)
3. S3 dispara automáticamente el **trigger** sobre la función Lambda
4. Lambda descarga la imagen, aplica un **filtro GaussianBlur** y una **marca de agua** con Pillow, y guarda el resultado en el **bucket de destino** con prefijo `procesada-`
5. El frontend hace **polling cada 3 segundos** (hasta 60s) usando `headObject` hasta confirmar que la imagen procesada ya existe
6. Se genera una **URL firmada** (presigned URL) y se muestra la imagen — el usuario puede descargarla

---

## 📁 Estructura del repositorio

```
taller-serverless-aws/
├── README.md
├── frontend/
│   └── index.html          # Interfaz web — sube imagen y muestra resultado
└── lambda/
    └── lambda_function.py  # Código de la función Lambda (Python + Pillow)
```

---

## ⚙️ Configuración AWS

### Fase 1 — Buckets S3

| Bucket | Propósito | Acceso |
|--------|-----------|--------|
| `imagenes-origen-bryanramirez` | Recibe imágenes del usuario | PUT público (CORS) |
| `imagenes-destino-bryanramirez` | Almacena imágenes procesadas | GET público (CORS) |

**CORS aplicado en ambos buckets:**
```json
[{
  "AllowedHeaders": ["*"],
  "AllowedMethods": ["PUT", "POST", "GET", "HEAD"],
  "AllowedOrigins": ["*"],
  "ExposeHeaders": ["ETag"]
}]
```

### Fase 2 — Función Lambda

| Parámetro | Valor |
|-----------|-------|
| Runtime | Python 3.12 |
| Timeout | 30 segundos |
| Layer | Pillow (Klayers) |
| Trigger | S3 → All object create events (bucket origen) |
| Variable de entorno | `BUCKET_DESTINO = imagenes-destino-bryanramirez` |

**Rol IAM (`lambda-procesador-imagenes-role`):**
- `s3:GetObject` sobre bucket origen
- `s3:PutObject` sobre bucket destino
- `AWSLambdaBasicExecutionRole` (logs en CloudWatch)

### Fase 3 — Integración frontend

El frontend implementa **polling activo** para detectar cuándo Lambda termina:

```javascript
for (let intento = 1; intento <= 20; intento++) {
  await new Promise(r => setTimeout(r, 3000)); // espera 3s
  try {
    await s3.headObject({ Bucket: BUCKET_DESTINO, Key: key_procesada }).promise();
    // ✅ imagen lista
    break;
  } catch (e) {
    // aún no está — continuar esperando
  }
}
```

Una vez confirmada la existencia, genera una **presigned URL** válida por 10 minutos y la muestra con opción de descarga.

---

## 🚀 Cómo usar

1. Clona este repositorio
2. Abre `frontend/index.html` en tu navegador (o despliégalo en el bucket de hosting S3)
3. Ingresa tus credenciales AWS:
   - **Access Key ID**
   - **Secret Access Key**
   - **Session Token** (solo si usas AWS Academy / Learner Lab)
4. Selecciona o arrastra una imagen (JPG, PNG, WEBP)
5. Haz clic en **"Subir imagen al bucket de origen"**
6. Espera mientras Lambda procesa — verás el progreso en tiempo real
7. Descarga la imagen procesada con el filtro blur y la marca de agua aplicados

> ⚠️ **AWS Academy:** Las credenciales expiran cada 4 horas. Copia siempre el Session Token completo desde el panel de Learner Lab.

---

## 🛠️ Tecnologías utilizadas

- **AWS S3** — Almacenamiento de objetos y hosting estático
- **AWS Lambda** — Cómputo serverless activado por eventos
- **AWS IAM** — Gestión de roles y políticas de seguridad
- **Python 3.12 + Pillow** — Procesamiento de imágenes en Lambda
- **AWS SDK for JavaScript v2** — Interacción con S3 desde el navegador
- **HTML5 / CSS3 / JavaScript** — Interfaz de usuario
