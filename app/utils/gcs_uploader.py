from google.cloud import storage

def subir_archivo_a_gcs(ruta_local, nombre_destino, bucket_name):
    """
    Sube un archivo local a un bucket de Google Cloud Storage
    y lo hace público.

    Args:
        ruta_local (str): Ruta al archivo en el sistema local.
        nombre_destino (str): Ruta/nombre dentro del bucket.
        bucket_name (str): Nombre del bucket GCS.

    Returns:
        str: URL pública del archivo subido.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(nombre_destino)

    # Sube el archivo
    blob.upload_from_filename(ruta_local)
    # Asegura que sea público
    blob.make_public()

    return blob.public_url
