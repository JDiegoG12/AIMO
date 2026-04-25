"""
Script de prueba rápida para la conexión con AWS Bedrock.
Uso: python test_bedrock.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── 1. Verificar variables de entorno ────────────────────────────────────────
print("=" * 50)
print("1. Verificando variables de entorno...")
print("=" * 50)

key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
secret  = os.getenv("AWS_SECRET_ACCESS_KEY", "")
region  = os.getenv("AWS_REGION", "us-east-1")
model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20251001:0")

print(f"  AWS_ACCESS_KEY_ID     : {'✓ presente (' + key_id[:8] + '...)' if key_id else '✗ FALTA'}")
print(f"  AWS_SECRET_ACCESS_KEY : {'✓ presente (' + secret[:4] + '...)' if secret else '✗ FALTA'}")
print(f"  AWS_REGION            : {region}")
print(f"  BEDROCK_MODEL_ID      : {model_id}")

if not key_id or not secret:
    print("\n✗ Faltan credenciales AWS. Agrégalas al .env y vuelve a intentar.")
    sys.exit(1)

# ── 2. Crear cliente boto3 ────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("2. Creando cliente boto3 bedrock-runtime...")
print("=" * 50)

try:
    import boto3
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
    )
    print("  ✓ Cliente creado correctamente")
except ImportError:
    print("  ✗ boto3 no está instalado. Ejecuta: pip install boto3")
    sys.exit(1)
except Exception as e:
    print(f"  ✗ Error al crear cliente: {e}")
    sys.exit(1)

# ── 3. Llamada de prueba a Bedrock ───────────────────────────────────────────
print("\n" + "=" * 50)
print(f"3. Probando invoke_model con {model_id}...")
print("=" * 50)

try:
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": "Responde solo con: Conexión exitosa."}]}],
        inferenceConfig={"maxTokens": 50, "temperature": 0.1},
    )
    text = response["output"]["message"]["content"][0]["text"]
    print(f"  ✓ Respuesta del modelo: {text.strip()}")
    print("\n✓ TODO OK — Bedrock está funcionando correctamente.")
except client.exceptions.UnrecognizedClientException:
    print("  ✗ UnrecognizedClientException: credenciales inválidas o token de seguridad incorrecto.")
    print("  → Si usas IAM User: verifica que AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY sean correctas.")
    print("  → Si usas credenciales temporales (SSO/AssumeRole): también necesitas AWS_SESSION_TOKEN en el .env")
    sys.exit(1)
except client.exceptions.AccessDeniedException:
    print("  ✗ AccessDeniedException: las credenciales son válidas pero no tienen permiso para usar Bedrock.")
    print("  → Verifica que el IAM user/role tenga la política 'AmazonBedrockFullAccess' o permiso 'bedrock:InvokeModel'.")
    sys.exit(1)
except Exception as e:
    error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    if "Could not connect" in str(e) or "endpoint" in str(e).lower():
        print("  → Verifica que AWS_REGION sea correcta y que tengas acceso a internet.")
    if "model" in str(e).lower() or "ResourceNotFoundException" in error_code:
        print(f"  → El modelo '{model_id}' puede no estar disponible en la región '{region}'.")
        print("  → Prueba cambiando BEDROCK_MODEL_ID en .env a: anthropic.claude-sonnet-4-5-20251001:0")
    sys.exit(1)
