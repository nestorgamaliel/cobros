from num2words import num2words

def monto_a_letras(monto):
    """Convierte un valor numérico a formato legal en español."""
    enteros = int(monto)
    # Extraer centavos
    centavos = int(round((monto - enteros) * 100))
    letras = num2words(enteros, lang='es').upper()
    return f"{letras} {centavos:02d}/100 DÓLARES DE LOS ESTADOS UNIDOS DE AMÉRICA"